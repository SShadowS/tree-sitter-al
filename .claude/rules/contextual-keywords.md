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
(`XmlPort` gives `(xmlport_keyword "xmlport")`, node text still `XmlPort`). The two exceptions,
`begin_keyword` (an external token) and `end_keyword` (a named one-token grammar rule since state
review C3), are childless leaves by design (below).

Why the alias: a named rule whose whole body is one token collapses into it, and a bare
`kw()` is a `token(PATTERN)`, which tree-sitter hides, so without the alias the node is a
childless leaf and the grammar ships two shapes. **Never put an ANONYMOUS `kw('begin')` /
`kw('end')` inside another rule** (the old fallback): a hidden pattern token is lexed and dropped
from the tree, which is how a complete `begin … end` inside every `#if` vanished until 4.0.0.

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

`tabledata_keyword` is a visible rule with the uniform shape since the losslessness pass; the
option-member sites take `_tabledata_identifier` (`alias(kw('tabledata'), $.identifier)`, ONE
rule: the generator names a shared unnamed token after its most-used alias), so that `identifier` is a leaf (`docs/deferred-work.md` item 27, pinned by `tools/tests/test_identifier_leaf.py`).

## `begin` is a scanner token; `end` is a named grammar token

`begin_keyword` is an external scanner token emitted at **every** `#if` depth. `end_keyword` is,
since state review C3, the named rule `end_keyword: $ => kw('end')`: a named rule whose body is one
token is a visible named **childless** leaf, exactly the node the external token gave (as an
external, `end` was in the follow set of every statement inside `begin..end` and of none outside,
which barred 2,178 state merges). Both are childless by design; do **not** "fix" `end_keyword` to
the `alias(kw(w), w)` form, which would add a child to every block end. There is exactly ONE
`kw('end')` in `grammar.js`, the rule body; every use site says `$.end_keyword` (a second
anonymous `kw('end')` also makes `generate` panic while `statement_names` lists `$.end_keyword`).

There is one way to read each word as a block keyword, so no scanner/literal pair for GLR to fork
on. The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get first
refusal; the scanner is asked before the lexer, so `PREPROC_SPLIT_END` decides before the grammar's
`end` (`.claude/rules/scanner.md`; design
`docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md`).

`end` is never a name where a statement starts: the reserved set `statement_names` (`code_names`
plus `$.end_keyword`, on `_expression_statement` and `_assign_target`) makes the version that
reads `end;` as a call die at once (issues #40/#41). Expressions keep `code_names`, so `End` as a
value is untouched. Declarations the reserved set cannot reach (a var section's next declaration,
a return-value name) are the scanner's `MALFORMED_DIRECTIVE` clause. Pinned by
`test/corpus/preproc_begin_end_named_test.txt` and `tools/config_oracle/tests/test_end_name_positions.py`.
