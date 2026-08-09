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

84 keywords are named nodes for query matching — 82 grammar rules plus the external `begin_keyword`/`end_keyword`. Use `kw()` (regex) for simple keywords:

```javascript
procedure_keyword: $ => kw('procedure'),
```

For CamelCase compound keywords, use explicit case variants:

```javascript
controladdin_keyword: $ => prec(10, choice(
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn'
)),
```

### Node shape is not uniform

A named rule whose whole body is a single token collapses *into* that token, so the token's visibility decides the node's shape:

> **A keyword node has an anonymous child if and only if its body reduces to a string literal. A pattern (`kw()`) or an external token gives a childless leaf.**

| body | child | count |
|---|---|---|
| bare `kw('word')` → `token(PATTERN)`, hidden | none — childless leaf | 51 |
| `alias(kw('word'), 'word')` → STRING | one anonymous `"word"` child | 18 |
| explicit `choice('x','X',…)` → STRING | one anonymous `"word"` child | 13 |
| external scanner token | none | 2 |

The `alias()` group exists because a bare `kw()` would have deleted the anonymous child those keywords previously had.

`node-types.json` **cannot** distinguish these: it lists anonymous children only when they sit inside a field, and none of these do, so all 84 look childless there. **Read a keyword's text from the node itself, never by descending into a child** — correct for all shapes, and it survives a rule moving between groups. Do not try to make the shapes uniform without a deliberate decision; it spans 84 rules and moves every consumer's anonymous layer.

## begin/end Named via Stateful Scanner

`begin_keyword` and `end_keyword` are external scanner tokens emitted at **every** `#if` depth. `grammar.js` carries no `kw('begin')`/`kw('end')` fallback — begin/end are scanner-exclusive, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach. See `docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md` for details.

The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get first refusal at depth > 0; both that and the named-keyword fallback are resolved inside a single scan.

**Never reintroduce a `kw('begin')`/`kw('end')` fallback.** Until 4.0.0 the depth > 0 path handed off to one, and a complete `begin … end` inside any `#if` block then landed in no node at all: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`) — unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and silently dropped.

This `.visible` rule applies to every `kw()` in the grammar: an anonymous `kw('word')` never produces a node of its own. Wrapping it in a named rule makes the *named* node visible, but the token inside stays hidden — see the shape table above.
