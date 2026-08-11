# Contextual Keywords

## V2 Architecture

In V2, most property/variable disambiguation is handled by the `PROPERTY_NAME` scanner token, not by keyword-level tricks. The scanner distinguishes `identifier =` (property) from `identifier :` (variable).

## Keyword-as-Identifier

Some AL keywords are used as identifiers in certain contexts. These are handled by the `keyword_as_identifier` rule, which mixes bare `kw()` tokens with references to existing keyword rules:

```javascript
keyword_as_identifier: $ => prec(-10, choice(
  kw('field'),
  $.key_keyword,
  kw('value'),
  kw('separator'),
  $.dataset_keyword,
  kw('type'),
  kw('version'),
  kw('action'),
  $.table_keyword,
  kw('assembly'),
)),
```

The `prec(-10)` makes this the last resort, so a real keyword use always wins.

**When adding to this list, use a bare `kw('x')` — do NOT reach for `$.x_keyword` even when one exists.** The rule reads the other way round from the obvious instinct, and the instinct is what produced the mixed list above. `keyword_as_identifier` is consumed as `alias($.keyword_as_identifier, $.identifier)`, so the node it produces claims to be a plain `identifier`, and a plain `identifier` is a **leaf**. A named alternative gives that "identifier" a named child, which no other `identifier` in the grammar has:

```
parameter name: identifier            <- `Type`,  bare kw('type')     — leaf, correct
parameter name: identifier
                  key_keyword         <- `Key`,   $.key_keyword       — named child
                    "key"
```

Three spellings (`Key`, `Table`, `Dataset`) currently do this and the other seven do not. That is a live two-shape inconsistency on `identifier`, the most common node type in the grammar; it is **not** fixed, and it is tracked separately because its fix direction is the opposite of the two below — here the uniform shape is the *leaf*, so it means demoting three named alternatives to bare `kw()`, not promoting seven.

Contrast `keyword_identifier` (no `as`), which is a distinct node type that exists precisely to say "a keyword stands here". There the named child is added information and all thirteen alternatives are named. **Which way a mixed choice should be made uniform depends on what the outer node claims to be**, so check that before converting either way.

## Named Keywords

117 keywords are named nodes for query matching — 115 grammar rules plus the external `begin_keyword`/`end_keyword`. Always wrap `kw()` in an `alias()` to the canonical lowercase spelling:

```javascript
procedure_keyword: $ => alias(kw('procedure'), 'procedure'),
```

For CamelCase compound keywords, use `kwCases()` — the first argument is the canonical form, the rest are the accepted spellings:

```javascript
controladdin_keyword: $ => prec(10, kwCases('controladdin',
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn',
  'ControlAddin', 'controlAddIn', 'controlAddin')),
```

**Never replace `kwCases()` with `kw()`.** The spelling whitelist is load-bearing: `kw()` is case-*insensitive* and would claim every permutation, stealing spellings AL code uses as identifiers (`eNuM: Decimal;` is a real variable declaration, and `eNuM` is deliberately absent from `enum_keyword`'s list). `test/corpus/enum_as_identifier_test.txt` catches this.

**The 13 `kwCases()` rules are exactly the object-declaration keywords, and nothing else:** `codeunit`, `controladdin`, `dotnet`, `enum`, `enumextension`, `pagecustomization`, `pageextension`, `permissionset`, `permissionsetextension`, `profileextension`, `reportextension`, `tableextension`, `xmlport`. That membership rule is a stronger check than the count, because it is falsifiable by inspection rather than by re-running a classifier. **A 14th entry that is not an object-declaration keyword is almost certainly a mistake** — `view_keyword` was miscounted into this set once precisely because it is not one.

### Node shape is uniform (since 4.0.0)

A named rule whose whole body is a single token collapses *into* that token, so the token's visibility decides the node's shape. A bare `kw('word')` is a `token(PATTERN)`, which tree-sitter hides, giving a childless leaf; `alias(…, 'word')` makes it a visible STRING. The grammar used to mix both, so a consumer could not predict a keyword's shape. It no longer does:

> **Every grammar keyword rule has exactly one anonymous child, typed as the canonical lowercase spelling. The 2 external tokens cannot take a child and remain childless leaves.**

| body | child | count |
|---|---|---|
| `alias(kw('word'), 'word')` → STRING | one anonymous `"word"` child | 102 |
| `kwCases('word', …)` → STRING, every spelling aliased to `'word'` | one anonymous `"word"` child | 13 |
| external scanner token | none — cannot take a child | 2 |

The child's type is the canonical lowercase spelling whatever the source used: `XmlPort` gives `(xmlport_keyword "xmlport")`, while the node's own text stays `XmlPort`.

`node-types.json` **cannot** confirm this: it lists anonymous children only when they sit inside a field, and none of these do, so all 117 look childless there. **Read a keyword's text from the node itself, never by descending into a child** — that stays correct for the two external tokens, which really are childless, and it survives any future change to the anonymous layer.

**`object_type_keyword` was the counter-example to the contract until it was fixed.** `node-types.json` contains **118** named `*_keyword` types, not 117 — `object_type_keyword` has no rule of its own; `database_reference` builds it by aliasing a six-way `choice` (`grep -n "object_type_keyword" grammar.js`). Five alternatives were named `$.*_keyword` rules carrying visible aliased STRING tokens while the sixth was a bare `kw('database')`, a hidden pattern token, so one node type shipped two shapes:

```
(object_type_keyword text='Page')      children=[("page", anonymous)]
(object_type_keyword text='DATABASE')  children=[]                     <- childless
```

**22,988 of 40,674 `object_type_keyword` nodes in BC.History were the childless kind.** Fixed by giving `database` a real `database_keyword` rule, like its five siblings; all 40,674 now carry exactly one anonymous child. Note the nested form `alias(alias(kw('database'), 'database'), $.object_type_keyword)` does **not** work — the aliases do not compose and the DATABASE case loses `object_type_keyword` altogether. A named rule is required.

`keyword_identifier` had the identical defect one level up (six named alternatives against seven bare `kw()`), and is fixed the same way. Both are pinned by fixtures in `test/corpus/`. **Neither was a byte gap, so `qc` reported nothing for either** — the outer node covered the bytes, which is why both outlived the losslessness work. The instrument that shows this class is a tree-cursor walk, not a coverage harness.

**Converting a bare `kw()` to `alias(kw(w), w)` cannot steal a spelling**, so the `kwCases()` warning above does not apply to it: `kw(w)` is `token(RustRegex('(?i)w'))` and `alias()` wraps that same token, leaving matching untouched. Measured over BC.History rather than argued — the `identifier` count was 5,908,480 before and after, and the `(parent, field, child)` edge census was byte-identical. `kwCases()` guards against *widening*; an alias widens nothing.

`_tabledata_keyword` is not in these counts: it is a *hidden* (`_`-prefixed) token helper rather than a keyword node, and `option_member` re-aliases it to `$.identifier`.

## begin/end Named via Stateful Scanner

`begin_keyword` and `end_keyword` are external scanner tokens emitted at **every** `#if` depth. `grammar.js` carries no `kw('begin')`/`kw('end')` fallback — begin/end are scanner-exclusive, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach. See `docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md` for details.

The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get first refusal at depth > 0; both that and the named-keyword fallback are resolved inside a single scan.

**Never reintroduce a `kw('begin')`/`kw('end')` fallback.** Until 4.0.0 the depth > 0 path handed off to one, and a complete `begin … end` inside any `#if` block then landed in no node at all: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`) — unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and silently dropped.

This `.visible` rule applies to every bare `kw()` in the grammar: an anonymous `kw('word')` never produces a node of its own. Wrapping it in a named rule makes the *named* node visible, but the token inside stays hidden — which is exactly why every keyword rule now adds an `alias()` to make that token visible. See the shape table above.
