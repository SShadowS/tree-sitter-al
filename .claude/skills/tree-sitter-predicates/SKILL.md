---
name: Tree-sitter Predicates and Directives
description: Reference for tree-sitter query predicates and directives (v0.25.x/0.26.x). Use when filtering query matches with #eq?, #match?, #any-of?, #is?, or when using directives like #set!, #offset!, #gsub!. Covers core predicates, Neovim/Helix extensions, quantified capture behavior, and custom predicate registration.
---

# Tree-sitter Predicates and Directives

Quick reference for predicates and directives. See `references/predicates.md` for detailed documentation.

## Predicates (filter matches)

| Predicate | Purpose | Example |
|-----------|---------|---------|
| `#eq?` | Text equals string/capture | `(#eq? @var "self")` |
| `#not-eq?` | Text doesn't equal | `(#not-eq? @var "self")` |
| `#match?` | Text matches regex | `(#match? @const "^[A-Z_]+$")` |
| `#not-match?` | Text doesn't match regex | `(#not-match? @var "^_")` |
| `#any-of?` | Text equals any of strings | `(#any-of? @kw "if" "else" "while")` |
| `#not-any-of?` | Text equals none of strings | `(#not-any-of? @var "self" "this")` |
| `#is?` | Has property | `(#is? definition)` |
| `#is-not?` | Doesn't have property | `(#is-not? local)` |

### Quantified Capture Variants (any- prefix)

| Predicate | Behavior |
|-----------|----------|
| `#any-eq?` | ANY node in capture equals |
| `#any-match?` | ANY node in capture matches |
| `#any-contains?` | ANY node contains substring |

## Directives (perform actions)

| Directive | Purpose | Example |
|-----------|---------|---------|
| `#set!` | Set metadata | `(#set! injection.language "sql")` |
| `#offset!` | Adjust capture range | `(#offset! @str 0 1 0 -1)` |

## Common Patterns

```scheme
; Match built-in identifiers
((identifier) @variable.builtin
  (#any-of? @variable.builtin "self" "this" "super"))

; Match SCREAMING_CASE constants
((identifier) @constant
  (#match? @constant "^[A-Z][A-Z_0-9]+$"))

; Compare two captures
((binary_expression
    left: (identifier) @left
    right: (identifier) @right)
  (#eq? @left @right))

; SQL injection in strings
((string) @injection.content
  (#match? @injection.content "^\\s*SELECT")
  (#set! injection.language "sql"))

; Set priority for overlapping matches
((identifier) @variable
  (#set! priority 90))
```

## Neovim Extensions

| Predicate | Purpose |
|-----------|---------|
| `#contains?` | Text contains substring |
| `#has-ancestor?` | Has ancestor of type |
| `#has-parent?` | Parent is type |
| `#lua-match?` | Lua pattern match |
| `#vim-match?` | Vim regex match |
| `#gsub!` | Transform text |
| `#trim!` | Trim whitespace |

## Binding Availability

| Predicate | Core | Neovim | Helix |
|-----------|------|--------|-------|
| `#eq?`, `#match?`, `#any-of?` | Yes | Yes | Yes |
| `#is?`, `#set!`, `#offset!` | Yes | Yes | Yes |
| `#contains?`, `#has-ancestor?` | No | Yes | Yes |
| `#lua-match?`, `#gsub!`, `#trim!` | No | Yes | No |
