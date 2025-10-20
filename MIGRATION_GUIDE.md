# Migration Guide: Rust-Style Attribute Refactor

**Version:** 2.0.0
**Breaking Change:** Parse tree structure for attributes has changed

## Overview

The tree-sitter-al grammar has been refactored to treat attributes as first-class statements (Rust/C# pattern) rather than embedded modifiers (C++ pattern). This resolves the long-standing limitation where attributes before preprocessor directives caused parse failures.

## For Grammar Consumers

### Parse Tree Changes

#### Old Structure (v1.x)

Attributes were nested within wrapper nodes:

```
(attributed_procedure
  (attribute_list
    (attribute
      attribute_name: (identifier)
      (attribute_arguments ...)))
  (procedure
    name: (name (identifier))
    ...))
```

#### New Structure (v2.0)

Attributes are sibling nodes to declarations:

```
(codeunit_declaration
  ...
  (attribute_item
    attribute: (attribute_content
      name: (identifier)
      arguments: (attribute_arguments ...)))
  (procedure
    name: (name (identifier))
    ...))
```

### Key Differences

| Aspect | Old (v1.x) | New (v2.0) |
|--------|------------|------------|
| **Node type** | `attributed_procedure`, `attributed_trigger`, etc. | `attribute_item` (uniform) |
| **Relationship** | Parent-child (nested) | Sibling (adjacent) |
| **Attribute list** | `attribute_list` with multiple `attribute` nodes | Individual `attribute_item` nodes |
| **Binding** | Implicit (wrapper contains both) | Explicit (requires semantic analysis) |

## Migration Steps

### 1. Update Tree Queries

**Old query (v1.x):**
```scm
(attributed_procedure
  (attribute_list) @attrs
  (procedure) @proc)
```

**New query (v2.0):**
```scm
; Match attribute followed by declaration
(
  (attribute_item) @attr
  .
  [
    (procedure)
    (trigger_declaration)
    (onrun_trigger)
  ] @decl
)
```

**Multiple attributes:**
```scm
; Match sequence of attributes before declaration
(
  (attribute_item)+ @attrs
  .
  (procedure) @proc
)
```

### 2. Implement Semantic Binding

Since attributes are now siblings to declarations, your tooling must associate them:

```python
def associate_attributes(tree):
    """Associate attribute_item nodes with following declarations."""
    attributes = []

    for node in tree.children:
        if node.type == 'attribute_item':
            attributes.append(node)
        elif node.type in ['procedure', 'trigger_declaration', 'variable_declaration']:
            if attributes:
                # Bind accumulated attributes to this declaration
                node.attributes = attributes
                attributes = []
        else:
            # Other node types clear pending attributes
            attributes = []
```

### 3. Handle Preprocessor Cases

Attributes can now appear before preprocessor directives:

```al
[Obsolete('Use NewAPI', '24.0')]
#if not CLEAN24
procedure OldAPI()
begin
end;
#endif
```

Parse tree:
```
(codeunit_declaration
  (attribute_item ...)
  (preproc_conditional_procedures
    (preproc_if ...)
    (procedure ...)
    (preproc_endif)))
```

The attribute binds to the procedure inside the `#if` block.

### 4. Update Node Type Checks

**Old code:**
```python
if node.type == 'attributed_procedure':
    attrs = node.child_by_field_name('attributes')
    proc = node.child_by_field_name('procedure')
```

**New code:**
```python
if node.type == 'procedure':
    # Look for preceding attribute_item siblings
    attrs = get_preceding_attributes(node)
    proc = node
```

## Supported Patterns

### ✅ Now Works: Attributes Before Preprocessor

```al
[IntegrationEvent(false, false)]
#if CLEAN25
procedure MyEvent()
begin
end;
#endif
```

This was the main limitation in v1.x and now works correctly!

### ✅ Multiple Attributes

```al
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent()
begin
end;
```

Each attribute appears as a separate `attribute_item` node.

### ✅ Attributes in Nested Contexts

```al
// Table fields
table 50100 MyTable
{
    fields
    {
        [ExternalName('ID')]
        field(1; "No."; Code[20]) { }
    }
}

// Parameters
procedure Test([Mandatory] Param: Integer) begin end;

// Enum values
enum 50100 Status
{
    [Caption('Active')]
    value(0; Active) { }
}
```

### ❌ No Longer Supported

Attributes with different values in preprocessor branches:

```al
// This pattern is no longer supported
#if CONDITION
[Attr1]
procedure Proc()
#else
[Attr2]
procedure Proc()
#endif
```

**Migration:** Place the common attribute outside:

```al
[Attribute]
#if CONDITION
procedure Proc()
#endif
```

## Testing Your Code

### Transition Strategy

1. **Dual-mode parser**: Support both v1.x and v2.0 parse trees during transition
2. **Feature detection**: Check for `attribute_item` node type to determine version
3. **Gradual migration**: Update one module at a time

### Example Feature Detection

```python
def detect_grammar_version(tree):
    """Detect which grammar version produced this tree."""
    for node in tree.walk():
        if node.type == 'attribute_item':
            return '2.0'
        if node.type.startswith('attributed_'):
            return '1.x'
    return 'unknown'
```

### Validation

Run your tooling against the test corpus:

```bash
# Clone the grammar repository
git clone https://github.com/your-org/tree-sitter-al
cd tree-sitter-al

# Checkout v2.0
git checkout v2.0.0-attribute-refactor

# Run tests
tree-sitter test

# Parse your AL files
tree-sitter parse path/to/your/file.al
```

## Common Migration Issues

### Issue 1: Missing Attributes

**Symptom:** Attributes not being detected

**Cause:** Still looking for `attributed_*` wrapper nodes

**Fix:** Update to scan for `attribute_item` siblings before declarations

### Issue 2: Incorrect Binding

**Symptom:** Attributes binding to wrong declaration

**Cause:** Not handling preprocessor directives correctly

**Fix:** Implement proper semantic analysis that follows AL scoping rules

### Issue 3: Multiple Attributes

**Symptom:** Only first attribute detected

**Cause:** Expecting single `attribute_list` node

**Fix:** Collect all consecutive `attribute_item` nodes before the declaration

## Benefits of v2.0

1. **✅ Fixed**: Attributes before preprocessor directives now work
2. **✅ Simpler grammar**: No `attributed_*` wrapper complexity
3. **✅ Consistent**: Same pattern (Rust/C#) across all contexts
4. **✅ Clearer parse trees**: Attributes and declarations at same level
5. **✅ Better maintainability**: Fewer special cases in grammar

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/your-org/tree-sitter-al/issues
- **Documentation**: See `CLAUDE.md` for implementation details
- **Test Examples**: See `test/corpus/phase3_attribute_preprocessor_test.txt` and `phase5_nested_attributes_test.txt`

## Timeline

- **v1.x**: Attributes as embedded modifiers (deprecated)
- **v2.0.0**: Rust-style attributes as first-class statements (current)
- **Migration period**: 6 months (v1.x and v2.0 supported in parallel)
- **v3.0.0**: v1.x support removed (planned)
