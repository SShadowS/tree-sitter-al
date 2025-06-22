# Known Issues

## Quoted Enum Types with Database Value

### Issue
When using a quoted identifier as an enum type followed by `::Database`, the parser fails to recognize it as a qualified enum value.

Example:
```al
TestField("Log Storage Type", "Log Storage Type"::Database);
```

The parser incorrectly parses `"Log Storage Type"` as a standalone quoted identifier and then fails on `::Database`.

### Root Cause
This is a fundamental limitation of tree-sitter's architecture where lexical analysis (tokenization) happens before parsing. The lexer tokenizes `"Log Storage Type"` as a complete `quoted_identifier` token before the parser can see that it's followed by `::` to form a qualified enum value.

The conflict arises because:
1. `DATABASE` is a keyword used in database references: `DATABASE::TableName`
2. `Database` can also be an enum value: `EnumType::Database`
3. The `kw('database', 5)` in `database_reference` creates a token with precedence that interferes with parsing `Database` as an enum value

### Workarounds
1. Use parentheses to force parsing:
   ```al
   TestField("Log Storage Type", ("Log Storage Type"::Database));
   ```

2. Use a variable:
   ```al
   var storageType: Enum "Log Storage Type";
   storageType := "Log Storage Type"::Database;
   TestField("Log Storage Type", storageType);
   ```

3. Avoid using `Database` as an enum value name

### Potential Solutions
1. **Scanner-based approach**: Implement a custom scanner to handle quoted identifiers followed by `::` differently
2. **Grammar restructuring**: Major refactoring to handle quoted identifiers at a higher level
3. **Post-processing**: Handle this case in the language server or other tooling

### Status
This issue affects a very specific edge case and has reasonable workarounds. A proper fix would require significant changes to the grammar architecture.