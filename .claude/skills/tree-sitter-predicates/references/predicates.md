# Tree-sitter Query Predicates and Directives Reference

A comprehensive guide to predicates and directives available in tree-sitter queries (versions 0.25.x/0.26.x).

## Overview

- **Predicates** end with `?` and filter/validate matches
- **Directives** end with `!` and perform actions or set metadata
- Predicates can be negated with `not-` prefix
- Quantified captures use `any-` prefix for "any match" behavior (default is "all must match")

---

## Query Syntax Essentials

### Basic Matching

```scheme
; Match a node type
(identifier)

; Match with children
(binary_expression (number_literal) (number_literal))

; Match anonymous nodes (tokens) with quotes
(binary_expression operator: "!=")
```

### Captures

```scheme
; Capture a node with @name
(identifier) @variable

; Multiple captures
(assignment_expression
  left: (identifier) @left
  right: (identifier) @right)
```

### Field Names

```scheme
; Match specific child by field name
(class_declaration
  name: (identifier) @class_name)
```

### Wildcards

```scheme
; (_) matches any named node
(call_expression function: (_) @func)

; _ matches any node (named or anonymous)
(array _ @element)
```

### Negated Fields

```scheme
; Match nodes that DON'T have a field
(class_declaration !type_parameters) @class
```

### Quantifiers

| Operator | Meaning | Example |
|----------|---------|---------|
| `?` | Optional (0 or 1) | `(decorator)? @dec` |
| `*` | Zero or more | `(comment)* @comments` |
| `+` | One or more | `(comment)+ @doc_comments` |

```scheme
; Match function with zero or more decorators
(decorator)* @decorators
(function_declaration) @function
```

### Alternations

```scheme
; Match any of several patterns
[
  (identifier) @function
  (member_expression property: (property_identifier) @method)
]

; Match any of several tokens
["break" "continue" "return"] @keyword
```

### Anchors

```scheme
; First child only (. at start)
(array . (identifier) @first_element)

; Last child only (. at end)
(block (_) @last_statement .)

; Immediate siblings (. between patterns)
(identifier) @prev . (identifier) @next
```

### Special Node Types

```scheme
; Match parser error nodes
(ERROR) @error

; Match zero-width inserted tokens
(MISSING) @missing

; Supertype matching (subtypes)
(expression/binary_expression) @binary
```

---

## Predicates

### Equality Predicates

#### `#eq?` / `#not-eq?`

Match capture text against a string or another capture.

```scheme
; Match specific identifier name
((identifier) @variable.builtin
  (#eq? @variable.builtin "self"))

; Compare two captures
((binary_expression
    left: (identifier) @left
    right: (identifier) @right)
  (#eq? @left @right))

; Negated form
((identifier) @variable
  (#not-eq? @variable "self"))
```

#### `#any-eq?` / `#any-not-eq?`

Match if ANY node in a quantified capture equals the value.

```scheme
; Match if any comment contains "TODO"
(((comment)+ @comment.todo)
  (#any-eq? @comment.todo "// TODO"))
```

---

### Pattern Matching Predicates

#### `#match?` / `#not-match?`

Match capture text against a regular expression.

```scheme
; Match SCREAMING_SNAKE_CASE constants
((identifier) @constant
  (#match? @constant "^[A-Z][A-Z_0-9]+$"))

; Match documentation comments
((comment) @comment.documentation
  (#match? @comment.documentation "^///"))

; Negated: exclude certain patterns
((identifier) @variable
  (#not-match? @variable "^_"))
```

**Note:** `^` and `$` anchors match the start/end of the captured node's text.

#### `#any-match?` / `#any-not-match?`

Match if ANY node in a quantified capture matches the pattern.

```scheme
; Match if any comment mentions TODO
(((comment)+ @comment.todo)
  (#any-match? @comment.todo "TODO|FIXME|XXX"))
```

#### `#lua-match?` / `#not-lua-match?` (Neovim)

Match using Lua patterns instead of regex.

```scheme
((identifier) @constant
  (#lua-match? @constant "^%u[%u_]+$"))
```

#### `#vim-match?` / `#not-vim-match?` (Neovim)

Match using Vim regex patterns.

```scheme
((identifier) @constant
  (#vim-match? @constant "\\v^[A-Z_]+$"))
```

---

### Set Membership

#### `#any-of?` / `#not-any-of?`

Efficiently check if capture matches one of several strings. Faster than multiple `#eq?` checks.

```scheme
; Match JavaScript built-in globals
((identifier) @variable.builtin
  (#any-of? @variable.builtin
    "arguments"
    "module"
    "console"
    "window"
    "document"
    "global"
    "process"))

; Match AL keywords that can be identifiers
((identifier) @keyword
  (#any-of? @keyword "begin" "end" "if" "then" "else"))
```

---

### Containment Predicates (Neovim)

#### `#contains?` / `#not-contains?`

Check if capture text contains a substring.

```scheme
; Match identifiers containing "test"
((identifier) @test
  (#contains? @test "test"))

; Match if contains any of multiple strings
((identifier) @foo_bar
  (#contains? @foo_bar "foo" "bar"))
```

#### `#any-contains?` / `#any-not-contains?`

Match if ANY node in quantified capture contains the string.

---

### Hierarchy Predicates (Neovim)

#### `#has-ancestor?` / `#not-has-ancestor?`

Check if the captured node has an ancestor of a specific type.

```scheme
; Match 'begin'/'end' only inside range expressions
((identifier) @variable.builtin
  (#any-of? @variable.builtin "begin" "end")
  (#has-ancestor? @variable.builtin range_expression))

; Match identifiers NOT inside a function
((identifier) @global
  (#not-has-ancestor? @global function_declaration))
```

#### `#has-parent?` / `#not-has-parent?`

Check the direct parent node type.

```scheme
; Match field identifiers in specific contexts
((field_identifier) @method
  (#has-parent? @method call_expression))

; Match identifiers not directly in assignments
((identifier) @variable
  (#not-has-parent? @variable assignment_expression))
```

---

### Property Predicates

#### `#is?` / `#is-not?`

Check if a capture has a specific property (set by `#set!`).

```scheme
; Only match if not a local variable
((identifier) @variable
  (#is-not? local))

; Match if marked as definition
((identifier) @definition
  (#is? definition))
```

---

## Directives

### `#set!`

Associate metadata with a pattern for programmatic access.

```scheme
; Set injection language
((comment) @injection.content
  (#match? @injection.content "^/\\*\\*")
  (#set! injection.language "markdown"))

; Set priority for overlapping matches
((identifier) @variable
  (#set! priority 90))

; Set arbitrary properties
((function_declaration
    name: (identifier) @function.name)
  (#set! kind "function")
  (#set! scope "module"))
```

Common `#set!` keys:
- `injection.language` - Language for injection
- `injection.combined` - Combine all matches for injection
- `injection.include-children` - Include child nodes in injection
- `priority` - Match priority (higher = more specific)
- `conceal` - Conceal character for display

---

### `#offset!`

Adjust the range of a captured node.

```scheme
; Offset: (capture, start_row, start_col, end_row, end_col)
; Trim first and last character from string content
((string) @string.content
  (#offset! @string.content 0 1 0 -1))

; Skip first line of a block
((block) @block.body
  (#offset! @block.body 1 0 0 0))
```

---

### `#gsub!` (Neovim)

Transform captured text using Lua pattern substitution.

```scheme
; Extract extension from filename
((identifier) @extension
  (#gsub! @extension ".*%.(.*)" "%1"))

; Remove prefix
((identifier) @name
  (#gsub! @name "^prefix_" ""))
```

---

### `#trim!` (Neovim)

Remove whitespace from captured nodes.

```scheme
; Trim blank lines from end (default behavior)
((block) @fold
  (#trim! @fold))

; Trim blank lines from both sides
; (#trim! @capture trim_start_line trim_start_char trim_end_line trim_end_char)
((block) @fold
  (#trim! @fold 1 0 1 0))

; Trim all whitespace
((string_content) @text
  (#trim! @text 1 1 1 1))
```

---

### `#select-adjacent!`

Filter captured nodes to only those adjacent to another capture.

```scheme
; Keep only comments adjacent to functions
((comment)+ @comment
  (function_declaration) @function
  (#select-adjacent! @comment @function))
```

---

### `#strip!`

Remove text matching a pattern from the capture.

```scheme
; Strip leading whitespace
((comment) @comment
  (#strip! @comment "^\\s+"))
```

---

## Quantified Capture Behavior

When a capture contains multiple nodes (via `+` or `*`):

| Predicate | Default Behavior | With `any-` Prefix |
|-----------|-----------------|-------------------|
| `#eq?` | ALL nodes must match | ANY node matches |
| `#match?` | ALL nodes must match | ANY node matches |
| `#contains?` | ALL nodes must match | ANY node matches |

```scheme
; Default: ALL comments must match
(((comment)+ @doc)
  (#match? @doc "^///"))

; With any-: ANY comment matches
(((comment)+ @has_todo)
  (#any-match? @has_todo "TODO"))
```

---

## Use Cases

### Syntax Highlighting

```scheme
; Highlight constants
((identifier) @constant
  (#match? @constant "^[A-Z][A-Z_0-9]+$"))

; Highlight built-in functions
((call_expression
    function: (identifier) @function.builtin)
  (#any-of? @function.builtin "print" "len" "range"))

; Documentation comments
((comment) @comment.documentation
  (#match? @comment.documentation "^///"))
```

### Code Injections

```scheme
; SQL in strings
((string
    (string_content) @injection.content)
  (#match? @injection.content "^\\s*SELECT")
  (#set! injection.language "sql"))

; Regex literals
((regex) @injection.content
  (#set! injection.language "regex"))
```

### Local Variable Tracking

```scheme
; Parameter definitions
(parameter
  name: (identifier) @local.definition)

; Variable references
((identifier) @local.reference
  (#is-not? local))
```

### Folding

```scheme
; Fold function bodies
((function_declaration
    body: (block) @fold))

; Fold comment blocks
(((comment)+ @fold)
  (#trim! @fold))
```

### Code Navigation (tags.scm)

```scheme
; Function definitions
(function_declaration
  name: (identifier) @name) @definition.function

; Class definitions
(class_declaration
  name: (identifier) @name) @definition.class

; Method calls
(call_expression
  function: (member_expression
    property: (property_identifier) @name)) @reference.call
```

---

## Implementation Notes

### Binding Differences

Not all predicates are available in all bindings:

| Predicate | Core C | Neovim | Web | Helix |
|-----------|--------|--------|-----|-------|
| `#eq?` | Yes | Yes | Yes | Yes |
| `#match?` | Yes | Yes | Yes | Yes |
| `#any-of?` | Yes | Yes | Yes | Yes |
| `#is?` | Yes | Yes | Yes | Yes |
| `#set!` | Yes | Yes | Yes | Yes |
| `#lua-match?` | No | Yes | No | No |
| `#vim-match?` | No | Yes | No | No |
| `#contains?` | No | Yes | No | No |
| `#has-ancestor?` | No | Yes | No | Yes |
| `#has-parent?` | No | Yes | No | Yes |
| `#gsub!` | No | Yes | No | No |
| `#offset!` | Yes | Yes | Yes | Yes |
| `#trim!` | No | Yes | No | No |

### Custom Predicates

Bindings may allow adding custom predicates:

```lua
-- Neovim example
vim.treesitter.query.add_predicate("custom-check?", function(match, pattern, bufnr, predicate)
  local node = match[predicate[2]]
  -- Return true/false
  return check_condition(node)
end)
```

---

## Version History

### Tree-sitter 0.25.x

- Stable query API
- Core predicates: `#eq?`, `#match?`, `#any-of?`, `#is?`, `#set!`
- Quantifiers fully supported

### Tree-sitter 0.26.x

- Performance improvements for query matching
- Better error messages for invalid queries
- Extended `#set!` metadata options

---

## Quick Reference

```scheme
; === PREDICATES ===
(#eq? @cap "value")           ; Text equals string
(#not-eq? @cap "value")       ; Text doesn't equal string
(#match? @cap "regex")        ; Text matches regex
(#not-match? @cap "regex")    ; Text doesn't match regex
(#any-of? @cap "a" "b" "c")   ; Text equals any of strings
(#not-any-of? @cap "a" "b")   ; Text equals none of strings
(#is? property)               ; Has property
(#is-not? property)           ; Doesn't have property

; Quantified capture variants (use "any-" prefix)
(#any-eq? @cap "value")       ; ANY node equals string
(#any-match? @cap "regex")    ; ANY node matches regex

; Neovim extensions
(#contains? @cap "substr")    ; Text contains substring
(#has-ancestor? @cap type)    ; Has ancestor of type
(#has-parent? @cap type)      ; Parent is of type
(#lua-match? @cap "pattern")  ; Lua pattern match

; === DIRECTIVES ===
(#set! key "value")           ; Set metadata
(#set! injection.language "sql")
(#set! priority 100)
(#offset! @cap 0 1 0 -1)      ; Adjust capture range
(#gsub! @cap "pat" "repl")    ; Transform text (Neovim)
(#trim! @cap)                 ; Trim whitespace (Neovim)
(#select-adjacent! @a @b)     ; Keep only adjacent matches
(#strip! @cap "pattern")      ; Remove matching text
```
