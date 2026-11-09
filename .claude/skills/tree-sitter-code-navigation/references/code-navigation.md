# Tree-sitter Code Navigation Reference

A comprehensive guide to implementing code navigation features using tree-sitter queries (versions 0.25.x/0.26.x). This covers tags queries, locals queries, definition/reference tracking, and scope analysis.

## Overview

Tree-sitter enables code navigation systems through its query language. The primary mechanisms are:

1. **Tags Queries** (`tags.scm`) - Identify definitions and references for navigation
2. **Locals Queries** (`locals.scm`) - Track variable scopes and bindings
3. **Combined Analysis** - Link definitions to references across files

GitHub's search-based code navigation is built on this foundation.

---

## Tags Queries

Tags queries identify **named entities** in source code for navigation features like "Go to Definition" and "Find References".

### Core Concepts

Each tag has two essential components:

| Component | Description | Examples |
|-----------|-------------|----------|
| **Role** | Entity's function | `definition`, `reference` |
| **Kind** | How entity is used | `class`, `function`, `method`, `variable` |

### Capture Naming Convention

```scheme
; Format: @role.kind with inner @name capture
(function_declaration
  name: (identifier) @name) @definition.function
```

The `@name` capture extracts the identifier text; the outer capture marks the entire construct.

### Standard Tag Vocabulary

#### Definitions

| Capture | Purpose |
|---------|---------|
| `@definition.class` | Class declarations |
| `@definition.function` | Function declarations |
| `@definition.interface` | Interface declarations |
| `@definition.method` | Method declarations |
| `@definition.module` | Module/namespace declarations |
| `@definition.type` | Type alias declarations |
| `@definition.constant` | Constant declarations |
| `@definition.field` | Field/property declarations |
| `@definition.parameter` | Function parameter declarations |
| `@definition.variable` | Variable declarations |

#### References

| Capture | Purpose |
|---------|---------|
| `@reference.call` | Function/method calls |
| `@reference.class` | Class references |
| `@reference.implementation` | Interface implementations |
| `@reference.type` | Type references |

### Complete Examples

#### Python

```scheme
; Function definitions
(function_definition
  name: (identifier) @name) @definition.function

; Class definitions
(class_definition
  name: (identifier) @name) @definition.class

; Method definitions
(class_definition
  body: (block
    (function_definition
      name: (identifier) @name) @definition.method))

; Function calls
(call
  function: (identifier) @name) @reference.call

; Method calls
(call
  function: (attribute
    attribute: (identifier) @name)) @reference.call
```

#### JavaScript/TypeScript

```scheme
; Function declarations
(function_declaration
  name: (identifier) @name) @definition.function

; Arrow function assigned to variable
(lexical_declaration
  (variable_declarator
    name: (identifier) @name
    value: (arrow_function))) @definition.function

; Class declarations
(class_declaration
  name: (identifier) @name) @definition.class

; Method definitions
(method_definition
  name: (property_identifier) @name) @definition.method

; Function assignment to property
(assignment_expression
  left: [(identifier) @name
         (member_expression
           property: (property_identifier) @name)]
  right: [(arrow_function) (function)]) @definition.function

; Function calls
(call_expression
  function: (identifier) @name) @reference.call

; Method calls
(call_expression
  function: (member_expression
    property: (property_identifier) @name)) @reference.call
```

#### AL (Business Central)

```scheme
; Procedure definitions
(procedure
  name: (identifier) @name) @definition.function

; Trigger definitions
(trigger
  name: (identifier) @name) @definition.function

; Table object
(table_object
  name: (identifier) @name) @definition.class

; Page object
(page_object
  name: (identifier) @name) @definition.class

; Codeunit object
(codeunit_object
  name: (identifier) @name) @definition.class

; Field definitions
(field
  name: (identifier) @name) @definition.field

; Procedure calls
(call_expression
  name: (identifier) @name) @reference.call
```

### Optional Captures

#### Documentation (`@doc`)

Capture docstrings for hover information:

```scheme
; Python docstrings
(function_definition
  name: (identifier) @name
  body: (block
    (expression_statement
      (string) @doc))) @definition.function

; JavaScript JSDoc
((comment) @doc
  (function_declaration
    name: (identifier) @name) @definition.function)
```

### Helper Directives

#### `#strip!`

Remove patterns from captured text:

```scheme
; Strip comment markers from docstrings
((comment) @doc
  (#strip! @doc "^#\\s*"))
```

#### `#select-adjacent!`

Filter to nodes adjacent to another capture:

```scheme
; Only keep comments directly before functions
((comment)+ @doc
  (function_definition) @definition.function
  (#select-adjacent! @doc @definition.function))
```

---

## Locals Queries

Locals queries track **variable scopes** for consistent highlighting and accurate reference resolution.

### Fixed Capture Names

Unlike tags queries, locals use a fixed vocabulary:

| Capture | Meaning |
|---------|---------|
| `@local.scope` | Node introduces a new local scope |
| `@local.definition` | Node contains a definition name |
| `@local.reference` | Node contains a name that may reference a definition |
| `@ignore` | Exclude from tagging (place before other patterns) |

### How Scope Tracking Works

1. Tree-sitter maintains a stack of scopes for each position
2. Each scope contains a set of definitions
3. When a `@local.reference` is found, it searches enclosing scopes for a matching definition
4. If found, both reference and definition receive the same highlighting

### Complete Examples

#### Ruby

```scheme
; Scope boundaries
(method) @local.scope
(do_block) @local.scope
(lambda) @local.scope
(block) @local.scope

; Definitions
(method_parameters
  (identifier) @local.definition)
(block_parameters
  (identifier) @local.definition)
(assignment
  left: (identifier) @local.definition)

; References
(identifier) @local.reference
```

#### JavaScript

```scheme
; Scopes
(function_declaration) @local.scope
(function) @local.scope
(arrow_function) @local.scope
(class_declaration) @local.scope
(for_statement) @local.scope
(for_in_statement) @local.scope
(block) @local.scope

; Definitions
(formal_parameters
  (identifier) @local.definition)
(variable_declarator
  name: (identifier) @local.definition)
(class_declaration
  name: (identifier) @local.definition)

; References
(identifier) @local.reference
```

#### Python

```scheme
; Scopes
(function_definition) @local.scope
(class_definition) @local.scope
(list_comprehension) @local.scope
(dictionary_comprehension) @local.scope
(set_comprehension) @local.scope
(generator_expression) @local.scope

; Definitions
(parameters
  (identifier) @local.definition)
(for_statement
  left: (identifier) @local.definition)
(assignment
  left: (identifier) @local.definition)
(as_pattern
  alias: (as_pattern_target) @local.definition)

; References
(identifier) @local.reference
```

#### AL (Business Central)

```scheme
; Scopes
(procedure) @local.scope
(trigger) @local.scope
(codeunit_object) @local.scope
(table_object) @local.scope
(page_object) @local.scope

; Definitions - var sections
(var_section
  (variable_declaration
    name: (identifier) @local.definition))

; Definitions - parameters
(parameter
  name: (identifier) @local.definition)

; Definitions - record fields
(field
  name: (identifier) @local.definition)

; References
(identifier) @local.reference
```

### Using `@ignore`

Exclude nodes from tagging before other patterns:

```scheme
; Ignore identifiers in certain contexts
(expression (identifier) @ignore)

; Then tag remaining identifiers as references
(identifier) @local.reference
```

### Integration with Highlights

Use `#is-not? local` to disable patterns for local variables:

```scheme
; Only highlight as function if not a local variable
((identifier) @function.call
  (#is-not? local))
```

---

## Scope Analysis Patterns

### Nested Scopes

```scheme
; Outer function scope
(function_declaration) @local.scope

; Inner block scopes (inherit from outer)
(block) @local.scope

; Lambda/closure scopes (capture outer variables)
(arrow_function) @local.scope
```

### Shadowing

Locals queries naturally handle variable shadowing - inner scope definitions take precedence:

```scheme
function outer() {
  let x = 1;           // @local.definition in outer scope
  function inner() {
    let x = 2;         // @local.definition in inner scope (shadows)
    console.log(x);    // @local.reference resolves to inner x
  }
  console.log(x);      // @local.reference resolves to outer x
}
```

### Hoisting (JavaScript)

For languages with hoisting, scope analysis still works because:
- `var` declarations are function-scoped (captured by function scope)
- `let`/`const` are block-scoped (captured by block scope)

---

## Testing

### Tags Testing

Place test files in `test/tags/` using comment annotations:

```ruby
# test/tags/test.rb
module Foo
  #     ^ definition.module
  class Bar
    #    ^ definition.class
    def baz
      #  ^ definition.method
    end
  end
end
```

### Running Tags Tests

```bash
# Test tags query against a file
tree-sitter tags src/example.py

# Output format: name, role, location, source line, docstring
```

Example output:
```
Foo       | definition.module | line 1, col 7  | module Foo      |
Bar       | definition.class  | line 2, col 8  | class Bar       |
baz       | definition.method | line 3, col 8  | def baz         |
```

### Locals Testing

Locals are tested indirectly through highlighting tests:

```javascript
// test/highlight/test.js
function test(param) {
  //           ^ variable.parameter
  let local = param;
  //  ^ variable
  //          ^ variable.parameter
  return local;
  //     ^ variable
}
```

---

## Editor Integration

### Neovim

Neovim's built-in LSP and treesitter integration uses these queries:

```lua
-- In after/queries/<language>/locals.scm
(function_declaration) @local.scope
(formal_parameters (identifier) @local.definition)
(identifier) @local.reference

-- In after/queries/<language>/tags.scm
(function_declaration
  name: (identifier) @name) @definition.function
```

### Helix

Helix uses similar query files in `runtime/queries/<language>/`:

```scheme
; locals.scm
(function_declaration) @local.scope
(variable_declarator name: (identifier) @local.definition)
```

### VS Code

VS Code extensions can use tree-sitter through:
- `vscode-anycode` for generic tree-sitter support
- Language-specific extensions with tree-sitter bindings

### GitHub Code Navigation

GitHub automatically uses `tags.scm` from grammar repositories:

1. Place queries in `queries/tags.scm`
2. Follow the standard vocabulary
3. GitHub indexes on push and enables:
   - Jump to definition
   - Find all references
   - Symbol search

---

## CLI Commands

### `tree-sitter tags`

```bash
# Basic usage
tree-sitter tags path/to/file.py

# Specify language scope
tree-sitter tags --scope source.python file.py

# Time the operation
tree-sitter tags -t file.py

# Test specific query file
tree-sitter tags -p /path/to/grammar file.py

# Quiet mode (no output, just validate)
tree-sitter tags -q file.py
```

### Options

| Option | Description |
|--------|-------------|
| `--scope` | Language scope to use |
| `-t, --time` | Print timing information |
| `-q, --quiet` | Suppress output |
| `-p, --grammar-path` | Path to grammar directory |
| `--config-path` | Alternative config file path |
| `-n, --test-number` | Run specific test |
| `-r, --rebuild` | Force parser rebuild |

---

## Configuration

### tree-sitter.json

Configure query paths in your grammar's `tree-sitter.json`:

```json
{
  "grammars": [
    {
      "name": "my_language",
      "scope": "source.mylang",
      "file-types": ["ml"],
      "highlights": "queries/highlights.scm",
      "locals": "queries/locals.scm",
      "tags": "queries/tags.scm"
    }
  ]
}
```

### Default Paths

If not specified, tree-sitter looks for:
- `queries/highlights.scm`
- `queries/locals.scm`
- `queries/tags.scm`

---

## Advanced Patterns

### Inherited Definitions

For class-based languages, capture inherited members:

```scheme
; Direct class definition
(class_declaration
  name: (identifier) @name) @definition.class

; Superclass reference
(class_declaration
  (class_heritage
    (identifier) @name)) @reference.class
```

### Generic Type Parameters

```scheme
; Type parameter definition
(type_parameters
  (type_parameter
    name: (identifier) @name)) @definition.type

; Type parameter reference
(generic_type
  (type_identifier) @name) @reference.type
```

### Namespace/Module Resolution

```scheme
; Qualified name resolution
(member_expression
  object: (identifier) @module
  property: (property_identifier) @name) @reference.call
```

### Import Tracking

```scheme
; Import creates local definition
(import_statement
  (import_clause
    (identifier) @name)) @definition.variable

; Named imports
(import_specifier
  (identifier) @name) @definition.variable
```

---

## Performance Considerations

### Query Optimization

1. **Specificity**: More specific patterns match faster
2. **Order**: Place common patterns first
3. **Avoid redundancy**: Don't capture the same node multiple times

```scheme
; Prefer specific patterns
(function_declaration
  name: (identifier) @name) @definition.function

; Over generic patterns with predicates
((identifier) @name
  (#has-parent? @name function_declaration))
```

### Incremental Updates

Tree-sitter's incremental parsing means:
- Only changed regions are re-parsed
- Navigation queries run on the updated tree
- Fast enough for real-time "as-you-type" features

---

## Version Notes

### Tree-sitter 0.25.x

- Stable query API
- Core predicates and directives
- Full quantifier support
- Tags and locals queries

### Tree-sitter 0.26.x

- Improved query performance
- Better error messages
- Extended `#set!` metadata
- Enhanced scope tracking

---

## Quick Reference

### Tags Query Template

```scheme
; === DEFINITIONS ===
(function_declaration
  name: (identifier) @name) @definition.function

(class_declaration
  name: (identifier) @name) @definition.class

(method_definition
  name: (property_identifier) @name) @definition.method

; === REFERENCES ===
(call_expression
  function: (identifier) @name) @reference.call

(call_expression
  function: (member_expression
    property: (property_identifier) @name)) @reference.call
```

### Locals Query Template

```scheme
; === SCOPES ===
(function_declaration) @local.scope
(class_declaration) @local.scope
(block) @local.scope

; === DEFINITIONS ===
(formal_parameters
  (identifier) @local.definition)
(variable_declarator
  name: (identifier) @local.definition)

; === REFERENCES ===
(identifier) @local.reference
```

### File Structure

```
queries/
  highlights.scm    # Syntax highlighting
  locals.scm        # Variable scope tracking
  tags.scm          # Code navigation
  injections.scm    # Language injections (optional)

test/
  highlight/        # Highlight tests
  tags/             # Tags tests
```
