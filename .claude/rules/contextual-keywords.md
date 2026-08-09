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

80 keywords are named rules for query matching. Use `kw()` (regex) for simple keywords:

```javascript
if_keyword: $ => kw('if'),
```

For CamelCase compound keywords, use explicit case variants:

```javascript
controladdin_keyword: $ => prec(10, choice(
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn'
)),
```

## begin/end Named via Stateful Scanner

`begin_keyword` and `end_keyword` are external scanner tokens emitted at **every** `#if` depth. `grammar.js` carries no `kw('begin')`/`kw('end')` fallback — begin/end are scanner-exclusive, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach. See `docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md` for details.

The depth counter decides only whether `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` get first refusal at depth > 0; both that and the named-keyword fallback are resolved inside a single scan.

**Never reintroduce a `kw('begin')`/`kw('end')` fallback.** Until 3.4.0 the depth > 0 path handed off to one, and a complete `begin … end` inside any `#if` block then landed in no node at all: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`) — unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and silently dropped.

This `.visible` rule applies to every `kw()` in the grammar: an anonymous `kw('word')` never produces a node. Only a `kw()` wrapped in a named rule (`if_keyword: $ => kw('if')`) is visible, and then the named node is a childless leaf.
