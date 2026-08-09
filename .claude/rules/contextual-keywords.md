# Contextual Keywords

## V2 Architecture

In V2, most property/variable disambiguation is handled by the `PROPERTY_NAME` scanner token, not by keyword-level tricks. The scanner distinguishes `identifier =` (property) from `identifier :` (variable).

## Keyword-as-Identifier

Some AL keywords are used as identifiers in certain contexts (e.g., `field`, `key`, `value`, `filter`, `action`, `type`, `version`). These are handled by the `keyword_as_identifier` rule:

```javascript
keyword_as_identifier: $ => choice(
  'field', 'key', 'value', 'separator', 'dataset', 'type', 'version', 'action'
),
```

When adding new keywords that can also be identifiers, add them to this choice list.

## Named Keywords

83 keywords are named nodes for query matching — 81 grammar rules plus the external `begin_keyword`/`end_keyword`. Always wrap `kw()` in an `alias()` to the canonical lowercase spelling:

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

### Node shape is uniform (since 4.0.0)

A named rule whose whole body is a single token collapses *into* that token, so the token's visibility decides the node's shape. A bare `kw('word')` is a `token(PATTERN)`, which tree-sitter hides, giving a childless leaf; `alias(…, 'word')` makes it a visible STRING. The grammar used to mix both, so a consumer could not predict a keyword's shape. It no longer does:

> **Every grammar keyword rule has exactly one anonymous child, typed as the canonical lowercase spelling. The 2 external tokens cannot take a child and remain childless leaves.**

| body | child | count |
|---|---|---|
| `alias(kw('word'), 'word')` → STRING | one anonymous `"word"` child | 68 |
| `kwCases('word', …)` → STRING, every spelling aliased to `'word'` | one anonymous `"word"` child | 13 |
| external scanner token | none — cannot take a child | 2 |

The child's type is the canonical lowercase spelling whatever the source used: `XmlPort` gives `(xmlport_keyword "xmlport")`, while the node's own text stays `XmlPort`.

`node-types.json` **cannot** confirm this: it lists anonymous children only when they sit inside a field, and none of these do, so all 83 look childless there. **Read a keyword's text from the node itself, never by descending into a child** — that stays correct for the two external tokens as well, and it survives any future change to the anonymous layer.

`_tabledata_keyword` is not in these counts: it is a *hidden* (`_`-prefixed) token helper rather than a keyword node, and `option_member` re-aliases it to `$.identifier`.

## begin/end Named via Stateful Scanner

`begin_keyword` and `end_keyword` are external scanner tokens emitted at **every** `#if` depth. `grammar.js` carries no `kw('begin')`/`kw('end')` fallback — begin/end are scanner-exclusive, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach. See `docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md` for details.

The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get first refusal at depth > 0; both that and the named-keyword fallback are resolved inside a single scan.

**Never reintroduce a `kw('begin')`/`kw('end')` fallback.** Until 4.0.0 the depth > 0 path handed off to one, and a complete `begin … end` inside any `#if` block then landed in no node at all: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`) — unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and silently dropped.

This `.visible` rule applies to every bare `kw()` in the grammar: an anonymous `kw('word')` never produces a node of its own. Wrapping it in a named rule makes the *named* node visible, but the token inside stays hidden — which is exactly why every keyword rule now adds an `alias()` to make that token visible. See the shape table above.
