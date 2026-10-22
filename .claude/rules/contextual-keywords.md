# Contextual Keywords

Property/variable disambiguation is the `PROPERTY_NAME` scanner token's job
(`.claude/rules/scanner.md`), not a keyword-level trick. The audit behind every rule here,
with its measured numbers, is `docs/keyword-shape-audit.md`.

## The rule that governs every mixed `choice()` of keywords

> **A `choice()` must not mix `$.x_keyword` with bare `kw('x')`: that ships one node type with
> two shapes. Which way you unify is decided by WHAT THE OUTER NODE CLAIMS TO BE, not by a
> house style.**

| outer node | it claims to be | uniform shape | direction |
|---|---|---|---|
| `keyword_identifier`, `object_type_keyword` | "a keyword stands here" | one named/anonymous child | **promote** the bare ones to named rules |
| `keyword_as_identifier` → `alias(…, $.identifier)` | a plain `identifier` | a **leaf** | **demote** the named ones to bare `kw()` |

Check the alias at the *use* site before converting either way. All three sites were fixed in
4.0.0 (half of all `object_type_keyword` nodes in BC.History had the wrong shape; a parameter
named `Table` was highlighted as a keyword 2,151 times) and each is pinned:
`test/corpus/object_type_keyword_uniform_shape_test.txt`,
`test/corpus/keyword_identifier_uniform_shape_test.txt`. **No byte gap, so `qc` saw nothing**;
the instrument for this class is `python tools/snip.py --census --root ./BC.History`.

**Keyword-as-identifier.** `keyword_as_identifier` (`prec(-10)`, the last resort) lists the
words AL uses as names in some contexts, and **every alternative is a bare `kw()`; adding a
`$.x_keyword` there is a bug even when the rule exists**, because the node is aliased to
`identifier` and an identifier is a leaf everywhere else. Adding a word: append `kw('x')`.
When touching it, verify both that the spurious highlight capture is gone *and* that the word
still captures at genuine keyword sites.

**`object_type_keyword` has no rule of its own**: `database_reference` builds it by aliasing a
six-way `choice` of named `*_keyword` rules (so `node-types.json` has one more named
`*_keyword` type than there are keyword rules). The nested form
`alias(alias(kw('database'), 'database'), $.object_type_keyword)` does **not** work: the
aliases do not compose and the node is lost. A named rule is required.

## Named keywords: one shape

Every grammar keyword rule is `alias(kw('word'), 'word')`, or `kwCases(...)` for compound
keywords, and has **exactly one anonymous child typed as the canonical lowercase spelling**
(`XmlPort` gives `(xmlport_keyword "xmlport")`, node text still `XmlPort`). The two external
tokens `begin_keyword`/`end_keyword` cannot take a child and are childless leaves.

Why the alias: a named rule whose whole body is one token collapses into it, and a bare
`kw()` is a `token(PATTERN)`, which tree-sitter hides, so without the alias the node is a
childless leaf and the grammar ships two shapes. **Never reintroduce a `kw('begin')`/`kw('end')`
fallback**: a hidden pattern token is lexed and dropped from the tree, which is how a complete
`begin … end` inside every `#if` vanished until 4.0.0.

**`node-types.json` cannot confirm the shape**: it lists anonymous children only inside a
field, so every keyword looks childless there. **Read a keyword's text from the node itself,
never by descending into a child.**

**`kwCases()` is an explicit spelling whitelist, each spelling aliased to the canonical form:**

```javascript
controladdin_keyword: $ => prec(10, kwCases('controladdin',
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn',
  'ControlAddin', 'controlAddIn', 'controlAddin')),
```

**Never replace `kwCases()` with `kw()`.** `kw()` is case-*insensitive* and would claim every
permutation, stealing spellings AL code uses as identifiers (`eNuM: Decimal;` is a real
variable; `test/corpus/enum_as_identifier_test.txt` catches it). **The 13 `kwCases()` rules are
exactly the object-declaration keywords, and nothing else:** `codeunit`, `controladdin`,
`dotnet`, `enum`, `enumextension`, `pagecustomization`, `pageextension`, `permissionset`,
`permissionsetextension`, `profileextension`, `reportextension`, `tableextension`, `xmlport`.
A 14th entry that is not an object-declaration keyword is almost certainly a mistake
(`view_keyword` was miscounted in once).

**Converting a bare `kw()` to `alias(kw(w), w)` cannot steal a spelling**: `alias()` wraps the
same token, so matching is unchanged (measured: identifier count and edge census byte-identical
over BC.History). The `kwCases()` warning is about *widening*; an alias widens nothing.

`tabledata_keyword` is a visible rule with the uniform shape since the losslessness pass; its
`option_member` site aliases it to `$.identifier`, the one remaining two-shape `identifier`
(`docs/deferred-work.md` item 27).

## begin/end are scanner tokens

`begin_keyword` and `end_keyword` are external scanner tokens emitted at **every** `#if`
depth; `grammar.js` has no fallback for them, so there is no scanner/literal pair for GLR to
fork on. The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get
first refusal, and both decisions happen inside one scan (`.claude/rules/scanner.md`; design
`docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md`).
