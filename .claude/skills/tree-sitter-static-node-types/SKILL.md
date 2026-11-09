---
name: Tree-sitter Static Node Types
description: Reference for tree-sitter node-types.json structure (v0.25.x/0.26.x). Use when working with generated type information, understanding parse tree node structure, implementing typed bindings for Rust/TypeScript, defining supertypes in grammar, or validating grammar changes via node-types.json diffs.
---

# Tree-sitter Static Node Types

Quick reference for node-types.json. See `references/static-types.md` for detailed documentation.

## What is node-types.json?

Auto-generated file (`src/node-types.json`) describing all possible node types after `tree-sitter generate`. Enables:
- Type generation for Rust/TypeScript
- Tooling with compile-time node structure knowledge
- Grammar validation and documentation

## Entry Structure

```json
{
  "type": "function_declaration",
  "named": true,
  "fields": {
    "name": {
      "multiple": false,
      "required": true,
      "types": [{ "type": "identifier", "named": true }]
    },
    "body": {
      "multiple": false,
      "required": true,
      "types": [{ "type": "block", "named": true }]
    }
  },
  "children": {
    "multiple": true,
    "required": false,
    "types": [{ "type": "decorator", "named": true }]
  }
}
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| `named: true` | Node from explicit grammar rule |
| `named: false` | Anonymous node (operators, keywords) |
| `fields` | Children accessed by field name |
| `children` | Unnamed children (by index) |
| `subtypes` | For supertypes: list of concrete types |

## Supertypes

Define in grammar.js:

```javascript
supertypes: $ => [
  $._expression,
  $._statement,
],
```

Appears in node-types.json:

```json
{
  "type": "_expression",
  "named": true,
  "subtypes": [
    { "type": "binary_expression", "named": true },
    { "type": "identifier", "named": true }
  ]
}
```

## Type Generation

### Rust

```rust
// Generated enum for supertype
pub enum Expression<'a> {
    BinaryExpression(BinaryExpression<'a>),
    Identifier(Identifier<'a>),
}

// Generated struct with field accessors
impl<'a> FunctionDeclaration<'a> {
    pub fn name(&self) -> Identifier<'a> { ... }
    pub fn body(&self) -> Block<'a> { ... }
}
```

### TypeScript

```typescript
type ExpressionNode = BinaryExpressionNode | IdentifierNode;

interface FunctionDeclarationNode extends SyntaxNode {
  nameNode: IdentifierNode;
  bodyNode: BlockNode;
}
```

## Validation Pattern

```bash
# Save before changes
cp src/node-types.json src/node-types.old.json

# Regenerate
tree-sitter generate

# Compare for breaking changes
diff src/node-types.old.json src/node-types.json
```
