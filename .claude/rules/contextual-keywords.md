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

`begin_keyword` and `end_keyword` are external scanner tokens emitted at depth 0 (outside `#if` blocks). At depth > 0, the scanner declines and anonymous `kw('begin')`/`kw('end')` tokens handle preprocessor-split contexts. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach. See `docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md` for details.
