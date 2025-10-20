# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Overview

This project provides a complete grammar definition for parsing AL (Application Language) source code, enabling syntax highlighting, code analysis, and language tooling support for Business Central development.

### Parser Status

Based on analysis of 15,358 AL files from the comprehensive Business Central production codebase, **15,266 files (99.4%) parse successfully**.

## Recent Changes

### v2.0.0 - Rust-Style Attribute Refactor (Breaking Change)
- **✅ FIXED:** Attributes before preprocessor directives now work correctly (`[Attr] #if COND procedure Proc() #endif`)
- **BREAKING:** Attributes are now first-class statements (parse tree structure changed)
- **IMPROVED:** Cleaner grammar, better maintainability, consistent with Rust/C# patterns
- **NEW:** Attributes supported on fields, parameters, and enum values
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for upgrade instructions
- See [PHASE4_UNSUPPORTED_PATTERNS.md](PHASE4_UNSUPPORTED_PATTERNS.md) for intentionally unsupported patterns

Recent improvements include:
- **Standalone semicolons in object properties** - Added support for empty statements (standalone semicolons) in table, field, and key property blocks, improving compatibility with existing AL code patterns
- **Date/time literals in filter expressions** - Added support for date literals (0D, 20240101D), time literals (120000T), and datetime literals (0DT) in CalcFormula filter expressions, with proper precedence to avoid parsing conflicts
- **StyleExpr as contextual keyword** - Fixed StyleExpr to be usable as a variable name in var sections, resolving parsing errors in page-level variable declarations
- **TestHttpRequestPolicy property** - Added support for TestHttpRequestPolicy property in codeunit declarations with BlockOutboundRequests value
- **ApiVersion as contextual keyword** - Added ApiVersion to the list of keywords that can be used as variable names, fixing parsing errors in var sections
- **Report preprocessor procedures** - Added support for #if/#endif conditional blocks around procedures in report objects, fixing ERROR nodes when procedures are wrapped in preprocessor directives
- **IsPreview keyword context handling** - Fixed conflict where IsPreview can now be used as both a property (`IsPreview = true;`) and a variable name (`var IsPreview: Boolean;`) through case-sensitive disambiguation
- **ShowAs property Standard value** - Added support for ShowAs = Standard in page actions, completing the set of valid values (SplitButton, Menu, Button, Standard)
- **UnknownValueImplementation property** - Added support for UnknownValueImplementation property in enum definitions for handling unknown enum values
- **OptionCaptionML with Locked** - Extended OptionCaptionML property to support Locked attribute (e.g., `OptionCaptionML = ENU='Value',Locked=true;`)
- **Namespace-qualified CalcFormula** - Added support for namespace-qualified table names in CalcFormula expressions (e.g., `CalcFormula = sum(Microsoft.CRM.Segment."Segment Line"."No. of Criteria Actions")`)
- **Ternary operator support** - Added comprehensive support for conditional/ternary expressions (`condition ? trueValue : falseValue`) in AL code
- **Namespace-qualified interface types** - Added support for namespace-qualified interface references in implements clauses and variable declarations
- **Preprocessor conditionals in Permissions property** - Added support for #if/#else/#endif directives within tabledata permission lists, enabling conditional compilation of permissions
- **Comprehensive preprocessor support** - Complete support for #if/#else/#endif directives throughout AL code, including split procedures, conditional object declarations, and complex trigger patterns
- **Views sections in page extensions** - Added support for views sections in pageextension objects with view definitions and modification patterns
- **ExternalName property** - Added support for ExternalName property in table fields with case-insensitive matching
- **Indentation properties** - Fixed IndentationColumn, IndentationControls, and ShowAsTree properties to be case-insensitive and accept field references (e.g., `Rec.Indentation`)
- **OnAfterLookup field trigger** - Added support for OnAfterLookup trigger in field sections with parameter support
- **AutoCalcField property** - Added support for AutoCalcField boolean property in report columns
- **ReadState property** - Added support for ReadState property in query objects (e.g., `ReadState = ReadUncommitted;`)
- **Trailing commas in Caption/OptionCaption** - Added support for trailing commas in Caption and OptionCaption properties (e.g., `Caption = 'text',;`)
- **End as identifier** - Fixed parsing of "End" and "EndingTime" as valid identifiers in assignment statements
- **Enabled property in keys** - Added support for Enabled property in table key declarations
- **AllowInCustomizations property** - Added support for AllowInCustomizations property with Never value and case-insensitive matching
- **SQL properties** - Added support for SqlDataType, SqlTimestamp, and TestTableRelation properties in table fields
- **OptionOrdinalValues property** - Added support for OptionOrdinalValues property with comma-separated integer lists including negative values
- **ExternalType property** - Added support for ExternalType property mapping AL field types to SQL data types (e.g., `ExternalType = Uniqueidentifier;`)
- **Multiline page link properties** - Fixed support for multiline SubPageLink/RunPageLink properties with boolean const values
- **Compressed property** - Added support for Compressed property in table fields with case-insensitive matching
- **Extended AutoFormatType values** - Added support for AutoFormatType property with any integer value (e.g., `AutoFormatType = 11;`)
- **DataItemTableFilter pipe syntax** - Added support for pipe-separated filter values in queries (e.g., `filter(Planned | "Firm Planned" | Released)`)
- **Case-insensitive property keywords** - Updated DeleteAllowed, InsertAllowed, ModifyAllowed, SourceTableTemporary, AutoFormatExpression to be case-insensitive
- **Performance optimizations** - Improved parser performance through optimized choice ordering and regex patterns
- **Preprocessor in enum extensions** - Added support for #if/#else/#endif directives within enumextension declarations
- **IsControlAddIn property** - Added support for IsControlAddIn property in dotnet type declarations
- **EntitySetCaption property** - Added support for EntitySetCaption property in query objects
- **Query computed columns** - Added support for computed columns in queries with Method properties (Count, Sum, etc.) using syntax like `column(LinesCount) { Method = Count; }`
- **RunObject qualified names** - Added support for fully qualified object names in RunObject property (e.g., `Page Microsoft.Manufacturing.StandardCost."Standard Cost Worksheet Names"`)
- **OptionOrdinalValues lists** - Added support for OptionOrdinalValues property with comma-separated integer lists including negative values (e.g., `-1, 0, 1`)
- **XMLPort enhancements** - Added Occurrence property (Required/Optional), OnBeforeInsertRecord trigger, and requestpage support for XMLPort objects
- **Preprocessor conditional var sections** - Added support for preprocessor conditionals (#if/#else/#endif) between procedure headers and code blocks for conditional variable declarations
- **Interface named return values** - Added support for named return values in interface procedures (e.g., `procedure Calculate() Result: Integer;`)
- **Query filter elements** - Added support for filter elements within query dataitems for advanced data filtering
- **OptimizeForTextSearch field property** - Added support for OptimizeForTextSearch property in table field declarations, enabling text search optimization at the field level
- **Preprocessor conditionals in using statements** - Added support for `#if not`, `#else`, and `#endif` directives within using statement sections for conditional compilation
- **Report column properties** - Created specialized property group for report columns with IncludeCaption, AutoFormatExpression, AutoFormatType, DecimalPlaces, and OptionCaption properties
- **Escaped double quotes in identifiers** - Added support for escaped double quotes (`""`) within quoted identifiers, enabling complex field names like `"BankAccReconLine.""Statement Amount"""`
- **ToolTip in area sections** - Added support for ToolTip property directly in action area sections for role center pages
- **SqlJoinType property** - Added support for SqlJoinType property in query and report dataitems with values InnerJoin, LeftOuterJoin, and CrossJoin
- **APIGroup and APIPublisher properties** - Extended APIGroup and APIPublisher properties from queries to page objects
- **RoleType property** - Added RoleType property support for entitlement objects with values Delegated and Local
- **Preprocessor in actions** - Added support for preprocessor directives (#if, #else, #endif) with 'not' operator in action sections
- **DefaultLayout property** - Added support for report DefaultLayout property with values like RDLC, Word, Excel
- **PermissionSetExtension objects** - Added support for permissionsetextension declarations with extends syntax
- **Entitlement objects** - Added support for entitlement declarations with ApplicationScope, PerUserServicePlan, and Role types
- **Query API properties** - Added support for EntityCaption, EntityName, EntitySetName, APIGroup, APIPublisher, APIVersion properties
- **Standalone semicolons in property contexts** - Added support for standalone semicolons in part sections, action blocks, and modify actions, significantly improving parsing compatibility
- **Empty option members** - Enhanced option types to support consecutive commas for empty members (e.g., `Option = 'Value1,,Value3';`)
- **ShowMandatory property expressions** - Enhanced ShowMandatory property to accept complex expressions like `NOT IsSaaSProd` instead of just boolean literals
- **RecordID case variation** - Added support for `RecordID` type with uppercase ID, complementing existing case variations
- **BigInteger literals** - Added support for BigInteger literals with L suffix (e.g., `0L`, `123L`, `-456L`)
- **Empty attribute arguments** - Fixed parsing of attributes with empty parentheses (e.g., `[TryFunction()]`)
- **ExecutionTimeout duration strings** - Added support for duration string format in ExecutionTimeout property (e.g., `'12:00:00'`, `'1.23:45:56.7890123'`)
- **ControlAddin attributed procedures** - Added support for attributes on ControlAddin procedures (e.g., `[Obsolete(...)]` on event procedures)
- **ExtendedDatatype Person value** - Added support for Person value in ExtendedDatatype property, used with Media and MediaSet fields
- **Preprocessor conditionals in table relations** - Enhanced table relations to support preprocessor conditionals with semicolons in conditional branches (e.g., `#if BC24 IF (...) Table1; #else IF (...) Table2; #endif`)
- **Pragma directive support in code blocks** - Added support for `#pragma warning disable/restore` directives within procedure code blocks
- **Namespace-qualified record types** - Added support for namespace-qualified table references in record variable declarations (e.g., `Record Microsoft.Foundation.UOM."Unit of Measure"`)
- **Unary plus operator** - Added support for unary `+` operator in expressions (e.g., `SignFactor := +1;`)
- **FOR...DOWNTO loops** - Added support for `DOWNTO` keyword in FOR statements (e.g., `FOR i := 10 DOWNTO 1 DO`)
- **StyleExpr comparison expressions** - Enhanced StyleExpr property to support comparison expressions with enum values (e.g., `StyleExpr = "Field" = "Field"::EnumValue;`)
- **ValuesAllowed mixed types** - Enhanced ValuesAllowed property to support both string literals and identifiers in comma-separated lists
- **OrderBy multiple fields** - Added support for OrderBy property with multiple fields in single directive (e.g., `OrderBy = ascending(Document_No_, Posting_Date);`)
- **Filter AND expressions** - Added support for combining filter conditions with & operator (e.g., `filter(<> "External User" & <> "Application" & <> "AAD Group")`)
- **Preprocessor conditional enums** - Added support for preprocessor conditionals around enum declarations with different implements clauses
- **String literal backslash support** - Fixed parsing of string literals containing backslash characters in function arguments
- **SubPageView table view syntax** - Enhanced SubPageView property to support full `sorting(...) where(...)` syntax
- **Report dataitem properties** - Added comprehensive support for DataItemTableView, RequestFilterFields, and RequestFilterHeading properties
- **StyleExpr boolean support** - Added boolean literal support to StyleExpr properties enabling `StyleExpr = TRUE;` syntax
- **AttentionAccent style value** - Enhanced style_value grammar to support AttentionAccent case-insensitive pattern
- **Complex property syntax** - Support for Caption and ToolTip properties with Comment parameters for multilingual applications
- **Page customization objects** - Full support for `pagecustomization` declarations with view modifications
- **Complete built-in function coverage** - All AL built-in functions across database, math, string, date/time categories
- **Advanced language constructs** - Interface operators, multi-dimensional arrays, range expressions
- **Extension objects** - Full support for page/table extensions and control add-ins
- **For loop enhancements** - Added support for field access and member expressions as loop variables (e.g., `for Rec.Index := 1 to 10`)
- **DataItemTableFilter comparisons** - Added support for comparison operators in DataItemTableFilter (e.g., `"Cost Amount (Actual)" = filter(> 0)`)
- **Query triggers** - Added trigger support to query objects including OnPreDataItem and other standard triggers
- **XMLPort triggers** - Added trigger support to XMLPort fieldattribute and tableelement nodes
- **Prompting area type** - Added support for 'prompting' area type in page actions for AI/Copilot features
- **Report extension dataset modifications** - Added support for addafter, addbefore, addfirst, addlast dataitem modifications in report extensions
- **Access property for fields** - Added support for Access property in table fields with values Internal/Public and case-insensitive matching

The parser successfully handles:
- All core AL object types (table, page, codeunit, enum, etc.)
- Page customizations with view filters and modifications
- Complex property declarations and configurations  
- Interface implementations and 'is'/'as' operators
- Comprehensive built-in function patterns
- Advanced triggers, procedures, and expression patterns

### Key Files

- **`grammar.js`**: The heart of the project - defines all AL language grammar rules
- **`test/corpus/`**: Comprehensive test suite with AL code examples and expected parse trees
- **`src/`**: Auto-generated C code for the parser (don't edit manually)

## Development Setup

### Prerequisites
- Node.js (v16+)
- tree-sitter CLI: `npm install -g tree-sitter-cli`

### Building the Parser
```bash
tree-sitter generate    # Generate parser from grammar.js
tree-sitter build      # Build native parser
```

## Usage

### Parsing AL Files
```bash
# Basic parsing
tree-sitter parse path/to/file.al

# Debug mode (shows detailed parse tree)
tree-sitter parse path/to/file.al --debug

# Quiet mode (only shows errors)
tree-sitter parse path/to/file.al --quiet
```

### Running Tests
```bash
# Run all grammar tests
tree-sitter test

# Test specific file patterns
tree-sitter test -f "table"
tree-sitter test -f "page_action"
```

### Interactive Development
```bash
# Start web-based playground
tree-sitter playground

# Watch mode for grammar development
tree-sitter generate --watch
```

## Testing

### Test Structure
Tests are located in `test/corpus/` with the format:
```
================================================================================
Test Description
================================================================================

[AL code to test]

--------------------------------------------------------------------------------

(expected_parse_tree)
```

### Adding Tests
1. Create new `.txt` file in `test/corpus/`
2. Follow the standard test format
3. Run `tree-sitter test` to validate
4. Use `tree-sitter parse` to generate expected parse tree

### Test Categories
- **Basic Objects**: `table.txt`, `codeunit.txt`, `page_type_variable.txt`
- **Advanced Features**: `page_action_groups.txt`, `enum_variables.txt`
- **Expressions**: `method_calls.txt`, `case_statements.txt`
- **Language Constructs**: `procedure_return_types.txt`, `exit_statements.txt`

## Contributing

### Grammar Development Guidelines
See [CONVENTIONS.md](CONVENTIONS.md) for detailed best practices including:
- Rule naming conventions (snake_case)
- Precedence handling
- Error recovery strategies
- Testing requirements

### Adding New Language Features
1. **Study the AL construct** - Understand syntax and semantics
2. **Check existing patterns** - Reuse similar grammar rules when possible
3. **Define grammar rules** - Add to appropriate section in `grammar.js`
4. **Create tests** - Add comprehensive test cases
5. **Test thoroughly** - Ensure no regressions in existing functionality

### Common Development Tasks
```bash
# Test changes
tree-sitter generate && tree-sitter test

# Debug specific AL code
echo "your AL code" | tree-sitter parse --debug

# Generate bindings
tree-sitter build --wasm  # WebAssembly
npm run build            # Native bindings
```

---

**Author**: Torben Leth (sshadows@sshadows.dk)  
**License**: MIT
