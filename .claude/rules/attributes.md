# Attribute Handling

## Architecture

Attributes are first-class statements using the Rust/C# pattern.

**Key points:**
- Attributes appear as `attribute_item` nodes in the parse tree
- They are siblings to declarations, not nested within them
- Preprocessor directives can appear between attributes and declarations
- Semantic analysis (post-parse) associates attributes with following declarations

## Parse Tree Structure

```
(attribute_item
  attribute: (attribute_content ...))
(procedure ...)
```

Attributes are separate nodes at the same level as declarations.

## Valid Patterns

```al
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent() begin end;

[Obsolete('Use NewVersion', '24.0')]
#if not CLEAN24
procedure OldVersion() begin end;
#endif

// Attributes on parameters
procedure Test([Mandatory] Param: Integer) begin end;

// Attributes on enum values
[Caption('Active')]
value(0; Active) { }

// Attributes on variables (in var sections)
[NonDebuggable]
MyVar: Integer;
```
