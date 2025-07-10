# Known Limitations

## Var Section and Attributed Procedure Conflict

**Update**: After extensive investigation including analysis by O3 model, this has been confirmed as a fundamental LR(1) parsing limitation that cannot be cleanly resolved without major restructuring that would break other valid patterns.

### Description
When a var section at the table/object level is followed by an attributed procedure, the parser may incorrectly try to parse the attribute as part of the var section, resulting in parsing errors.

### Example Pattern That Fails
```al
table 50000 "Test"
{
    var
        Config: Record "Config";

    [BusinessEvent(false, false)]  // Parser tries to parse this as attributed_variable_declaration
    procedure OnBeforeAction()
    begin
        // ...
    end;
}
```

### Root Cause
This is a fundamental limitation of LR(1) parsing without lookahead. When the parser is inside a `var_section` and encounters `[`, it has to decide whether this is:
1. An attributed variable declaration (e.g., `[RunOnClient] x: Integer;`)
2. The start of an attributed procedure that follows the var section

Without lookahead, the parser cannot distinguish these cases and commits to `attributed_variable_declaration`, which then fails when it encounters `procedure` instead of a variable declaration.

### Why It's Hard to Fix
1. **Context Sensitivity**: The same pattern `[Attribute]` means different things in different contexts
2. **No Lookahead**: Tree-sitter's LR(1) parser cannot peek ahead to see what follows the attribute
3. **Valid Use Cases**: Attributed variables ARE valid inside procedure-level var sections, so we can't simply remove the capability

### Attempted Solutions and Why They Failed
1. **External Scanner**: The parser commits to a path before the scanner can intervene
2. **Removing attributed_variable_declaration**: Breaks legitimate procedure var sections with `[RunOnClient]`
3. **Negative Precedence**: Makes the parser avoid attributed variables even when it should use them
4. **Separate var section rules**: Would require major grammar restructuring and break compatibility
5. **O3's strict context separation**: While theoretically sound, implementation breaks valid patterns like preprocessor directives in var sections
6. **Removing preproc_conditional_variables from var_section**: Breaks tests that legitimately use preprocessor in var sections

### Workarounds

#### Option 1: Add a Comment
```al
var
    Config: Record "Config";

// End var section
[BusinessEvent(false, false)]
procedure OnBeforeAction()
```

#### Option 2: Empty Statement
```al
var
    Config: Record "Config";
    ;  // Extra semicolon forces var section to end

[BusinessEvent(false, false)]
procedure OnBeforeAction()
```

#### Option 3: Move Var Section
```al
table 50000 "Test"
{
    [BusinessEvent(false, false)]
    procedure OnBeforeAction()
    var
        LocalVar: Text;
    begin
        // ...
    end;

    var
        Config: Record "Config";
}
```

### Affected Test Cases
As of the last run, these test cases are affected by this limitation:
- Var section followed by attributed procedure in preprocessor
- Test attribute preproc split procedure  
- Preprocessor interrupting var section with procedure
- Multiple var sections with preprocessor procedure between
- Var section with preprocessor containing only attribute and procedure start

### Future Considerations
A future major version of the grammar could potentially:
1. Use different rules for table-level vs procedure-level var sections
2. Implement a more sophisticated external scanner with better lookahead
3. Restructure the grammar to avoid the ambiguity

However, these would be breaking changes requiring significant refactoring.