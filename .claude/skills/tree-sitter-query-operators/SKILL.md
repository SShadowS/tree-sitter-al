---
name: Tree-sitter Query Operators
description: Reference for tree-sitter query operators (v0.25.x/0.26.x). Use when writing tree-sitter queries with captures (@), fields (:), negated fields (!), wildcards (_ and (_)), quantifiers (+, *, ?), grouping, alternation ([]), anchors (.), anonymous nodes, or special nodes (ERROR, MISSING). Covers operator syntax, precedence, and version-specific features.
---

# Tree-sitter Query Operators

Quick reference for query operators. See `references/operators.md` for detailed documentation.

## Operator Summary

| Operator | Syntax | Purpose |
|----------|--------|---------|
| Capture | `(node) @name` | Associate name with matched node |
| Field | `field: (child)` | Match specific child relationship |
| Negated Field | `!field` | Match node lacking field |
| Named Wildcard | `(_)` | Match any named node |
| Any Wildcard | `_` | Match any node (including anonymous) |
| One or More | `(pattern)+` | Match 1+ occurrences |
| Zero or More | `(pattern)*` | Match 0+ occurrences |
| Optional | `(pattern)?` | Match 0 or 1 occurrence |
| Grouping | `(a b)+` | Apply quantifier to sequence |
| Alternation | `[a b c]` | Match any alternative |
| First Anchor | `. child` | Child must be first |
| Last Anchor | `child .` | Child must be last |
| Adjacent | `a . b` | Immediate siblings |
| Anonymous | `"token"` | Match literal token |
| Error | `(ERROR)` | Match parse errors |
| Missing | `(MISSING)` | Match error recovery nodes |

## Common Patterns

```scheme
; Capture with field
(function_declaration
  name: (identifier) @func_name
  body: (block) @func_body) @function

; Multiple captures in pattern
(binary_expression
  left: (_) @left
  operator: "+" @op
  right: (_) @right)

; Alternation for operators
(binary_expression
  operator: ["+" "-" "*" "/"] @operator)

; Quantified captures
(comment)+ @doc_comments

; Adjacent siblings (comment before function)
(comment) @doc . (function_declaration) @function

; First/last child
(array . (_) @first)
(array (_) @last .)

; Negated field (no return type)
(function_declaration !return_type) @void_function
```

## Version Features

- **v0.25.x**: `(MISSING)` and `(MISSING type)` support, supertype validation
- **v0.26.x**: Performance improvements, better error messages
