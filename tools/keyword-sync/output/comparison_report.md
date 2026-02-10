# Keyword Synchronization Report

Generated: 2026-02-10 01:54:38
VS Code AL Extension: v17.0.2107262

## Summary

| Metric | Count |
|--------|-------|
| VS Code keywords | 308 |
| Grammar keywords | 669 |
| Common (matched) | 301 |
| Missing in grammar | 0 |
| False positives | 7 |
| Extra in grammar | 368 |

**Coverage**: 100.0% of VS Code keywords are in grammar (including false positives handled by generic mechanisms)

## False Positives

Keywords flagged as 'missing' but handled by generic grammar mechanisms,
external scanner tokens, or not used in production AL files.

| Keyword | Category | Reason |
|---------|----------|--------|
| `downto` | control_flow | Handled by external scanner token `for_downto_keyword` (grammar.js externals) |
| `program` | control_flow | Legacy C/AL keyword not used in modern AL (Business Central) |
| `runonclient` | control_flow | Attribute handled by generic `attribute_item` rule: [RunOnClient] |
| `securityfiltering` | control_flow | Attribute handled by generic `attribute_item` rule: [SecurityFiltering(...)] |
| `suppressdispose` | control_flow | Attribute handled by generic `attribute_item` rule: [SuppressDispose] (not used in production) |
| `to` | control_flow | Handled by external scanner token `for_to_keyword` (grammar.js externals) |
| `withevents` | control_flow | Attribute handled by generic `attribute_item` rule: [WithEvents] |

## Extra Keywords in Grammar

Keywords in grammar.js but not in VS Code extension. These may be:
- Valid additions specific to tree-sitter parsing
- Obsolete keywords that could be removed
- Aliases or variations

*368 keywords - showing first 50*

| Keyword | Type | Precedence |
|---------|------|------------|
| `access` | choice_operator | - |
| `always` | kw | - |
| `attention` | kw | - |
| `autocalcfield` | kw | - |
| `both` | kw | - |
| `closingdates` | kw | - |
| `columns` | kw | - |
| `compressiontype` | kw | - |
| `defaultnamespace` | kw | - |
| `edit` | kw | - |
| `enddata` | kw | - |
| `extensible` | choice_operator | - |
| `favorable` | kw | - |
| `float` | kw | - |
| `flowtemplateid` | kw | - |
| `global` | kw | - |
| `includedpermissionsets` | kw | - |
| `indentationcolumn` | kw | - |
| `leftouterjoin` | kw | - |
| `linkedobject` | kw | - |
| `lookuppageid` | kw | - |
| `maxlength` | kw | - |
| `minvalue` | kw | - |
| `msdos` | kw | - |
| `navigationpane` | kw | - |
| `nonrestrictedproperties` | kw | - |
| `numeric` | kw | - |
| `onafterinsertevent` | kw | - |
| `ondelete` | kw | - |
| `ondrilldown` | kw | - |
| `oninsert` | kw | - |
| `onlookup` | kw | - |
| `onmodify` | kw | - |
| `pdf` | kw | - |
| `permissions` | choice_operator | - |
| `read` | kw | - |
| `return` | kw | - |
| `runformlinktype` | kw | - |
| `runobject` | kw | - |
| `showcaption` | kw | - |
| `splitbutton` | kw | - |
| `string` | kw | - |
| `systemactions` | kw | - |
| `tab` | kw | - |
| `tabletype` | kw_with_eq | - |
| `unfavorable` | kw | - |
| `usagecategory` | kw | - |
| `varchar` | kw | - |
| `windows` | kw | - |
| `zero` | kw | - |

## Special Handling Reference

Some keywords require special handling per project guidelines:

### Operators (use `choice()` not `kw()`)
```javascript
// These conflict with expressions when using kw()
choice('and', 'AND', 'And')
choice('or', 'OR', 'Or')
choice('not', 'NOT', 'Not')
choice('xor', 'XOR', 'Xor')
choice('div', 'DIV', 'Div')
choice('mod', 'MOD', 'Mod')
```

### Contextual Keywords (use `kw_with_eq()`)
```javascript
// Property names that conflict with variable names
kw_with_eq('ispreview')  // Matches 'ispreview=' including the equals
kw_with_eq('helplink')  // Matches 'helplink=' including the equals
kw_with_eq('description')  // Matches 'description=' including the equals
```

### Literal Exceptions
```javascript
// When kw_with_eq() doesn't work, use literal strings
// 'tabletype' - use choice('tabletype', 'TABLETYPE', 'Tabletype')
// 'style' - use choice('style', 'STYLE', 'Style')
// 'styleexpr' - use choice('styleexpr', 'STYLEEXPR', 'Styleexpr')
// 'visible' - use choice('visible', 'VISIBLE', 'Visible')
// 'filters' - use choice('filters', 'FILTERS', 'Filters')
```
