# Keyword Synchronization Report

Generated: 2026-02-02 10:53:27
VS Code AL Extension: v17.0.2037090

## Summary

| Metric | Count |
|--------|-------|
| VS Code keywords | 308 |
| Grammar keywords | 668 |
| Common (matched) | 300 |
| Missing in grammar | 8 |
| Extra in grammar | 368 |

**Coverage**: 97.4% of VS Code keywords are in grammar

## Missing Keywords

Keywords found in VS Code AL extension but not in grammar.js.

### Control Flow (Priority 1)

| Keyword | Special Handling | Source |
|---------|------------------|--------|
| `downto` | kw | tmlanguage |
| `indataset` | kw | tmlanguage |
| `program` | kw | tmlanguage |
| `runonclient` | kw | tmlanguage |
| `securityfiltering` | kw | tmlanguage |
| `suppressdispose` | kw | tmlanguage |
| `to` | kw | tmlanguage |
| `withevents` | kw | tmlanguage |

## Extra Keywords in Grammar

Keywords in grammar.js but not in VS Code extension. These may be:
- Valid additions specific to tree-sitter parsing
- Obsolete keywords that could be removed
- Aliases or variations

*368 keywords - showing first 50*

| Keyword | Type | Precedence |
|---------|------|------------|
| `accessbypermission` | kw | - |
| `additionalsearchterms` | kw | - |
| `apigroup` | kw | - |
| `autoupdate` | kw | - |
| `both` | kw | - |
| `caption` | kw_with_eq | - |
| `closingdates` | kw | - |
| `comment` | kw | - |
| `decimalplaces` | kw | - |
| `defaultimplementation` | kw | - |
| `drilldownpageid` | kw | - |
| `edit` | kw | - |
| `embedding` | kw | - |
| `endindex` | kw | - |
| `endvalue` | kw | - |
| `externalname` | kw | - |
| `float` | kw | - |
| `formatevaluate` | kw | 20 |
| `includecaption` | kw_with_eq | - |
| `iscontroladdin` | kw | - |
| `locked` | kw | - |
| `maintainsqlindex` | kw | - |
| `minvalue` | kw | - |
| `msdos` | kw | - |
| `multiline` | kw | - |
| `nonrestrictive` | kw | - |
| `nonstandard` | kw | - |
| `nvarchar` | kw | - |
| `onafterdeleteevent` | kw | - |
| `onbeforeinsertevent` | kw | - |
| `onmodify` | kw | - |
| `onrun` | kw | - |
| `processing` | kw | - |
| `promoted` | kw | - |
| `promotedcategory` | kw | - |
| `rdlc` | kw | - |
| `requestfilterheading` | kw | - |
| `showcaption` | kw | - |
| `sqljointype` | kw | - |
| `state` | kw | - |
| `string` | kw | - |
| `tableseparator` | kw | - |
| `tooltipml` | kw | - |
| `unbound` | kw | - |
| `unknownvalueimplementation` | kw | - |
| `update` | kw | - |
| `usagecategory` | kw | - |
| `utf8` | kw | - |
| `variable` | kw | 1 |
| `zeroormany` | kw | 1 |

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
