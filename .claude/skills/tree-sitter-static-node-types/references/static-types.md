# Tree-Sitter Static Node Types Reference

A comprehensive guide to static node types in Tree-sitter 25.x/26.x. Use this skill when working with `node-types.json`, generating typed bindings, or understanding the structure of Tree-sitter parse trees.

## Quick Reference

| Concept | Description |
|---------|-------------|
| `node-types.json` | Auto-generated file describing all possible node types in a grammar |
| Named nodes | Nodes derived from named rules (show in tree output) |
| Anonymous nodes | Nodes from string literals (parentheses, operators, keywords) |
| Supertypes | Abstract categories grouping related node types |
| Fields | Named child positions within a node |

## What Are Static Node Types?

Static node types provide structured, machine-readable type information about every possible syntax node in a Tree-sitter grammar. This enables:

1. **Type generation** - Create strongly-typed bindings for Rust, TypeScript, etc.
2. **Tooling** - IDEs and linters can know valid node structures at compile time
3. **Validation** - Verify grammar produces expected node shapes
4. **Documentation** - Self-documenting node structure

The system generates a `node-types.json` file during `tree-sitter generate` that describes every possible syntax node.

---

## node-types.json Structure

### File Location

After running `tree-sitter generate`, find it at:
```
<grammar-dir>/src/node-types.json
```

### Basic Entry Format

Each node type is an object with core fields:

```json
{
  "type": "string_literal",
  "named": true
}
```

**Fields:**
- **`type`** - String matching the grammar rule name (corresponds to `ts_node_type()`)
- **`named`** - Boolean indicating if node derives from a named rule or string literal

**Uniqueness constraint:** The combination of `type` and `named` must be unique across the file.

### Named vs Anonymous Nodes

```json
[
  {
    "type": "identifier",
    "named": true
  },
  {
    "type": "+",
    "named": false
  },
  {
    "type": "if",
    "named": false
  }
]
```

- **Named nodes** (`"named": true`) - From explicit grammar rules like `identifier: $ => /[a-z]+/`
- **Anonymous nodes** (`"named": false`) - From string literals like `'+'`, `'if'`, `'('`

---

## Internal Nodes (Nodes with Children)

Nodes that have children include additional properties describing their structure.

### Fields Property

Maps field names to child type descriptors:

```json
{
  "type": "method_definition",
  "named": true,
  "fields": {
    "body": {
      "multiple": false,
      "required": true,
      "types": [
        { "type": "statement_block", "named": true }
      ]
    },
    "name": {
      "multiple": false,
      "required": true,
      "types": [
        { "type": "identifier", "named": true },
        { "type": "property_identifier", "named": true }
      ]
    },
    "decorator": {
      "multiple": true,
      "required": false,
      "types": [
        { "type": "decorator", "named": true }
      ]
    },
    "parameters": {
      "multiple": false,
      "required": true,
      "types": [
        { "type": "formal_parameters", "named": true }
      ]
    }
  }
}
```

**Child type descriptor fields:**
- **`required`** - Boolean: must at least one node of this type exist?
- **`multiple`** - Boolean: can multiple nodes of this type exist?
- **`types`** - Array of possible node types with `type` and `named` keys

### Children Property

For unnamed children (not accessed via field):

```json
{
  "type": "array",
  "named": true,
  "fields": {},
  "children": {
    "multiple": true,
    "required": false,
    "types": [
      { "type": "_expression", "named": true },
      { "type": "spread_element", "named": true }
    ]
  }
}
```

**Usage:**
- `fields` describes children accessed via `node.child_by_field_name("name")`
- `children` describes children accessed via `node.children(cursor)` or `node.named_child(index)`

---

## Supertype Nodes

Abstract rule categories (expressions, types, declarations) can be registered in the grammar's `supertypes` list.

### Defining Supertypes in Grammar

```javascript
module.exports = grammar({
  name: 'my_language',

  supertypes: $ => [
    $._expression,
    $._declaration,
    $._type,
  ],

  rules: {
    _expression: $ => choice(
      $.binary_expression,
      $.unary_expression,
      $.call_expression,
      $.identifier,
    ),
    // ...
  }
});
```

### Supertype Entries in node-types.json

```json
{
  "type": "_expression",
  "named": true,
  "subtypes": [
    { "type": "binary_expression", "named": true },
    { "type": "unary_expression", "named": true },
    { "type": "call_expression", "named": true },
    { "type": "identifier", "named": true }
  ]
}
```

### Benefits of Supertypes

1. **Compression** - Instead of listing all expression types in every `types` array, reference the supertype once
2. **Abstraction** - Type generators can create abstract base types
3. **Maintainability** - Adding new expression types automatically propagates

**Before supertypes:**
```json
"types": [
  { "type": "binary_expression", "named": true },
  { "type": "unary_expression", "named": true },
  { "type": "call_expression", "named": true },
  { "type": "identifier", "named": true }
]
```

**With supertypes:**
```json
"types": [
  { "type": "_expression", "named": true }
]
```

---

## Type Generation for Languages

### Rust Type Generation

Tree-sitter can generate Rust types from `node-types.json`:

```bash
tree-sitter generate --build
```

This creates strongly-typed node accessors in the generated bindings:

```rust
// Generated types
pub struct MethodDefinition<'a> {
    node: Node<'a>,
}

impl<'a> MethodDefinition<'a> {
    pub fn body(&self) -> StatementBlock<'a> {
        // Required field - returns node directly
    }

    pub fn name(&self) -> MethodName<'a> {
        // Returns enum of possible types
    }

    pub fn decorator(&self) -> impl Iterator<Item = Decorator<'a>> {
        // Multiple field - returns iterator
    }
}

// Supertype becomes enum
pub enum Expression<'a> {
    BinaryExpression(BinaryExpression<'a>),
    UnaryExpression(UnaryExpression<'a>),
    CallExpression(CallExpression<'a>),
    Identifier(Identifier<'a>),
}
```

### Node.js/TypeScript

For TypeScript projects, use the types from `node-types.json` to create type definitions:

```typescript
// types.d.ts - generated or hand-written from node-types.json

interface SyntaxNode {
  type: string;
  isNamed: boolean;
  // ...
}

interface MethodDefinitionNode extends SyntaxNode {
  type: 'method_definition';
  bodyNode: StatementBlockNode;
  nameNode: IdentifierNode | PropertyIdentifierNode;
  decoratorNodes: DecoratorNode[];
}

// Supertype union
type ExpressionNode =
  | BinaryExpressionNode
  | UnaryExpressionNode
  | CallExpressionNode
  | IdentifierNode;
```

### Web (WASM) Bindings

For web usage, `node-types.json` helps generate typed wrappers around the WASM parser.

---

## Practical Usage Patterns

### Querying node-types.json Programmatically

```javascript
const nodeTypes = require('./src/node-types.json');

// Find all named nodes
const namedNodes = nodeTypes.filter(n => n.named);

// Find nodes with specific field
const nodesWithBody = nodeTypes.filter(n =>
  n.fields && n.fields.body
);

// Find supertypes
const supertypes = nodeTypes.filter(n => n.subtypes);

// Get all possible children of a node type
function getChildTypes(typeName) {
  const node = nodeTypes.find(n => n.type === typeName && n.named);
  if (!node) return [];

  const types = new Set();

  // From fields
  if (node.fields) {
    for (const field of Object.values(node.fields)) {
      field.types.forEach(t => types.add(t.type));
    }
  }

  // From children
  if (node.children) {
    node.children.types.forEach(t => types.add(t.type));
  }

  return [...types];
}
```

### Validating Grammar Changes

Compare `node-types.json` before and after grammar changes to detect breaking changes:

```bash
# Save old types
cp src/node-types.json src/node-types.old.json

# Generate new
tree-sitter generate

# Compare
diff src/node-types.old.json src/node-types.json
```

### Generating Documentation

Use `node-types.json` to auto-generate node documentation:

```python
import json

with open('src/node-types.json') as f:
    types = json.load(f)

for t in types:
    if not t.get('named'):
        continue

    print(f"## {t['type']}")

    if t.get('fields'):
        print("\n### Fields\n")
        for name, field in t['fields'].items():
            req = "required" if field['required'] else "optional"
            mult = "multiple" if field['multiple'] else "single"
            types_str = ", ".join(x['type'] for x in field['types'])
            print(f"- **{name}** ({req}, {mult}): {types_str}")

    if t.get('children'):
        children = t['children']
        types_str = ", ".join(x['type'] for x in children['types'])
        print(f"\n### Children: {types_str}")

    if t.get('subtypes'):
        types_str = ", ".join(x['type'] for x in t['subtypes'])
        print(f"\n### Subtypes: {types_str}")

    print()
```

---

## Recent Features (Tree-sitter 0.20+)

### Improved Supertype Handling

Supertypes now properly handle:
- Nested supertypes (supertype containing other supertypes)
- Inline rules within supertypes
- Better deduplication of type entries

### Field Presence Tracking

More accurate `required` field detection:
- Accounts for `optional()` wrappers
- Handles `choice()` branches where field may not appear
- Correctly marks fields in `repeat()` as `multiple: true, required: false`

### Anonymous Node Preservation

String literals in grammar are preserved with their exact text:

```json
{
  "type": "&&",
  "named": false
}
```

---

## Common Patterns

### Multiple Possible Types for a Field

When a field can hold different node types:

```json
{
  "type": "assignment_expression",
  "named": true,
  "fields": {
    "left": {
      "multiple": false,
      "required": true,
      "types": [
        { "type": "identifier", "named": true },
        { "type": "member_expression", "named": true },
        { "type": "subscript_expression", "named": true }
      ]
    }
  }
}
```

### Optional Fields

```json
{
  "type": "function_declaration",
  "named": true,
  "fields": {
    "return_type": {
      "multiple": false,
      "required": false,
      "types": [
        { "type": "type_annotation", "named": true }
      ]
    }
  }
}
```

### Repeating Fields

```json
{
  "type": "class_body",
  "named": true,
  "fields": {},
  "children": {
    "multiple": true,
    "required": false,
    "types": [
      { "type": "method_definition", "named": true },
      { "type": "field_definition", "named": true }
    ]
  }
}
```

---

## Debugging Tips

### Missing Node Types

If a node type is missing from `node-types.json`:
1. Check if the rule is hidden (starts with `_`)
2. Verify the rule is reachable from the root
3. Run `tree-sitter generate` to regenerate

### Unexpected Fields

If fields appear that shouldn't:
1. Check for `field()` wrappers in grammar
2. Look for inherited fields from `choice()` alternatives
3. Verify `alias()` usage

### Type Conflicts

If `type`/`named` pairs conflict:
1. Rename the grammar rule
2. Use `alias()` to differentiate
3. Check for unintentional rule reuse

---

## Related Files in This Project

- `src/node-types.json` - Generated node types for this grammar
- `grammar.js` - Grammar definition that produces node types
- `src/parser.c` - Generated parser (references node types)

---

## References

- [Tree-sitter Documentation: Static Node Types](https://tree-sitter.github.io/tree-sitter/using-parsers/6-static-node-types.html)
- [Tree-sitter API: Type Checking](https://tree-sitter.github.io/tree-sitter/using-parsers/1-getting-started.html)
- [Grammar DSL Reference](https://tree-sitter.github.io/tree-sitter/creating-parsers/3-writing-the-grammar.html)
