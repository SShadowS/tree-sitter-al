# Missing AL Grammar Elements

This document lists elements that are currently missing from the tree-sitter-al grammar. Items are organized by type (properties, syntax constructs, etc.).

## Status Update (May 25, 2025)

Recent progress:
- ✅ SourceTableView property is fully implemented with support for SORTING, WHERE, and ORDER clauses
- ✅ Separator action element is fully implemented
- ✅ All high priority field properties have been implemented (DecimalPlaces, LookupPageId, OptionCaption, TableRelation)
- ✅ Several medium priority field properties implemented (AssistEdit, ColumnSpan, DrillDown, HideValue, Importance)
- ✅ DATABASE references are now fully supported (e.g., DATABASE::Customer and DATABASE::"Sales Header")

Remaining critical items:
- ✅ Page-level trigger declarations
- ✅ AL built-in functions/methods (SETCURRENTKEY, SETRANGE, etc.)
- Expression types (enum comparisons, method chaining)

The documentation for these properties can be found in this directory "U:\Git\BCDoc\properties"
You are allowed to read them if you need more information about the properties.

When changes have been made to the grammar, please update this document accordingly.

Compile the grammar with the command `tree-sitter generate` to ensure the changes are reflected in the generated parser.
At task is NEVER complete until 'tree-sitter generate' has been run and the grammar has been tested.

To test the changes, you can use the command `tree-sitter test` to run the tests defined in the grammar's test suite.

To test the parser with a specific file, you can use the command `tree-sitter parse <file>` to see how the parser interprets the file.

Always use "generate" before "test" to ensure the latest changes are included in the parser.

## Page Object Properties

All page object properties have been implemented. ✓

## Page Field Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| AssistEdit | Boolean | Enables the assist-edit button for the field. | Medium | ✓ Implemented |
| AutoFormatExpression | String | Defines a custom format expression for the field. | Medium |
| AutoFormatType | Integer/Enum | Specifies a standard format type for the field. | Medium |
| BlankNumbers | Boolean/String | Controls how blank numbers are displayed. | Medium |
| BlankZero | Boolean | Controls whether zero values are displayed as blank. | Medium |
| CharAllowed | String | Restricts input to specified characters. | Medium |
| ClosingDates | Boolean | Controls whether dates are validated against accounting periods. | Medium |
| ColumnSpan | Integer | Defines how many columns the field spans. | Medium | ✓ Implemented |
| DateFormula | Boolean | Indicates the field contains a date formula. | Medium |
| DecimalPlaces | Integer:Integer | Defines precision and scale for decimal values. | High | ✓ Implemented |
| DrillDown | Boolean | Enables drill-down functionality for the field. | Medium | ✓ Implemented |
| DrillDownPageId | Page ID | Specifies the page ID to open when drilling down. | Medium |
| ExtendedDatatype | PhoneNo/URL/Email/Ratio/Duration/Masked | Provides additional data type semantics. | Medium |
| HideValue | Boolean | Hides the value but shows the caption. | Low | ✓ Implemented |
| Importance | Standard/Additional/Promoted | Controls field visibility in different form factors. | Medium | ✓ Implemented |
| LookupPageId | Page ID | Specifies the page ID to open for lookups. | High | ✓ Implemented |
| MaxValue | Expression | Defines the maximum allowed value. | Medium |
| MinValue | Expression | Defines the minimum allowed value. | Medium |
| MultiLine | Boolean | Enables multi-line text editing. | Medium |
| NavigationPageId | Page ID | Specifies the page to navigate to. | Medium |
| NotBlank | Boolean | Prevents blank values in the field. | Medium |
| Numeric | Boolean | Restricts input to numeric values. | Medium |
| ODataEDMType | String | Defines the EDM type for OData. | Low |
| OptionCaption | String | Provides captions for option values. | High | ✓ Implemented |
| OptionCaptionML | Multi-language Value | Multi-language version of OptionCaption. | Medium |
| QuickEntry | Boolean | Controls whether the field is included in quick entry. | Medium |
| RowSpan | Integer | Defines how many rows the field spans. | Medium |
| ShowCaption | Boolean | Controls whether the field caption is shown. | Medium |
| ShowMandatory | Boolean | Shows the field as mandatory even if it's not required. | Medium |
| SignDisplacement | Boolean | Controls display of the sign for numeric values. | Low |
| Style | Standard/StandardAccent/Strong/StrongAccent/etc. | Controls the visual style of the field. | Medium |
| StyleExpr | String Expression | Dynamic expression for the field style. | Medium |
| TableRelation | Table Relation Expression | Defines a relationship to another table. | High | ✓ Implemented |
| Title | Boolean | Indicates the field should be displayed as a title. | Low |
| ValuesAllowed | String List | Restricts the field to a list of allowed values. | Medium |

## Page Action Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| Ellipsis | Boolean | Shows an ellipsis in the action caption. | Low |
| Gesture | String | Defines a keyboard gesture for the action. | Low |
| InFooterBar | Boolean | Places the action in the footer bar. | Medium |
| IsHeader | Boolean | For action separators, indicates it's a header. | Low |
| RunPageMode | Edit/View/Create | Specifies the mode to use when running a page. | Medium |
| RunPageOnRec | Boolean | Uses the current record when running the page. | Medium |

## Page Part Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| Multiplicity | One/Many | Defines the multiplicity of the part. | Medium |
| Provider | String | Specifies a provider for the part. | Low |
| ShowFilter | Boolean | Controls whether filters are shown on the part. | Medium |
| UpdatePropagation | No/Updated | Controls how updates propagate to the parent page. | Medium |

## Page Group Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| CuegroupLayout | String | Defines the layout for a cue group. | Medium |
| FreezeColumn | String | Freezes columns in a repeater group. | Medium |
| GridLayout | Boolean | Enables grid layout for the group. | Medium |
| IndentationColumn | String | Defines the column used for indentation. | Low |
| IndentationControls | String List | Defines the controls to indent. | Low |
| ShowAsTree | Boolean | Displays the group as a tree structure. | Medium |
| TreeInitialState | CollapseAll/ExpandAll | Controls the initial expansion state of a tree. | Medium |

## Page Custom Action Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| CustomActionType | String | Defines the type of custom action. | Medium |
| AllowedFileExtensions | String | For file uploads, defines allowed file extensions. | Medium |
| AllowMultipleFiles | Boolean | For file uploads, allows multiple files. | Medium |
| FileUploadAction | String | Defines an action for file uploads. | Medium |
| FileUploadRowAction | String | Defines a row action for file uploads. | Medium |

## Page View Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| Filters | Filter Expression | Defines filters for a page view. | Medium |
| OrderBy | Field List | Defines the sort order for a page view. | Medium |
| SharedLayout | Boolean | Indicates the view shares the layout with the primary view. | Low |

## Critical Missing AL Grammar Elements

The following elements cause parsing failures in actual AL code files:

### Missing Object-Level Properties

| Property | Expected Value Type | Description | Priority |
|----------|-------------------|-------------|----------|
| SourceTableView | Complex Expression | Defines sorting and filtering of the source table | Critical | ✓ Implemented |

Example:
```al
SourceTableView = SORTING("Source Document", "Source No.")
                  WHERE("Source Document" = CONST("Sales Order"));
```

### Missing Action Elements

| Element | Description | Priority |
|---------|-------------|----------|
| separator | Creates a visual separator between actions | High | ✓ Implemented |

Example:
```al
separator(Separator1)
{
}
```

### Missing Page Elements

| Element | Description | Priority |
|---------|-------------|----------|
| Page-level trigger declarations | Triggers like OnAfterGetRecord not being parsed correctly | Critical |

### Missing AL Built-in Functions/Methods

The following AL built-in methods are not properly supported:

| Function/Method | Description | Priority |
|-----------------|-------------|----------|
| SETCURRENTKEY() | Sets the current key for record iteration | High |
| SETRANGE() | Sets a filter range on a field | High |
| FINDFIRST | Finds the first record | High |
| FINDSET | Finds a set of records | High |
| ISEMPTY | Checks if a record set is empty | High |
| SETFILTER() | Sets a complex filter | High |
| RUNMODAL | Runs a page/report modally | High |
| CONFIRM() | Shows a confirmation dialog | High |
| SETTABLEVIEW() | Sets a table view on a report | High |
| SETRECFILTER | Sets record filter | High |
| GETVIEW() | Gets the current view | High |

### Missing Expression Types

| Expression Type | Description | Priority |
|-----------------|-------------|----------|
| DATABASE::"Table Name" | Database object references | High | ✓ Implemented |
| Status enum comparisons | E.g., SalesHeader.Status::Open | High |
| Method chaining | Complex method chains like object.method().property | High |

## Grammar Design Patterns

When implementing properties in the tree-sitter-al grammar, follow these conventions for consistency:

### 1. Property Value Rules

- **Simple Boolean Properties**: Use direct reference to `$.boolean` without creating intermediate value rules
  ```javascript
  property_name_property: $ => seq(
    'PropertyName',
    '=',
    field('value', $.boolean),
    ';'
  )
  ```

- **Simple Integer Properties**: Typically use direct reference to `$.integer`, but may create value rule for future extensibility
  ```javascript
  property_name_property: $ => seq(
    'PropertyName',
    '=',
    field('value', $.integer), // Direct reference
    ';'
  )
  ```

- **Enum Properties**: Always create dedicated value rule with case-insensitive matching
  ```javascript
  property_name_value: $ => choice(
    /[oO][pP][tT][iI][oO][nN]1/,
    /[oO][pP][tT][iI][oO][nN]2/
  ),
  
  property_name_property: $ => seq(
    'PropertyName',
    '=',
    field('value', $.property_name_value),
    ';'
  )
  ```

- **Complex Types**: Create specific value rules for complex types or properties that might be extended in the future

### 2. Property Rule Structure

- Use consistent naming: `property_name_property` for the property rule
- Use consistent naming: `property_name_value` for the value rule (if needed)
- Always include a semicolon in the property rule
- Use field('value', ...) to capture the value

### 3. Integration Points

For each new property, add it to all relevant sections:
- Add to the property value rules (if needed)
- Add to the property rules section
- Add to all applicable field_section patterns
- Add to the property choice list

## Implementation Progress

### Completed
- **Phase 1 (High Priority Page Properties)**: 
  - AboutText & AboutTextML
  - AboutTitle & AboutTitleML
  - CardPageId
  - DeleteAllowed, InsertAllowed, ModifyAllowed
  - SourceTableTemporary

- **Phase 2A (Medium Priority Boolean Page Properties)**:
  - AnalysisModeEnabled
  - AutoSplitKey
  - ChangeTrackingAllowed
  - DelayedInsert
  - LinksAllowed
  - MultipleNewLines
  - PopulateAllFields

- **Phase 2B (Medium Priority Complex Page Properties)**:
  - DataAccessIntent
  - DataCaptionExpression
  - InstructionalText & InstructionalTextML

- **Phase 3 (High Priority Field Properties)**:
  - DecimalPlaces
  - LookupPageId
  - OptionCaption
  - TableRelation

- **Phase 4A (High + Medium Priority Page Properties)**:
  - AccessByPermission
  - AdditionalSearchTerms
  - PromptMode
  - RefreshOnActivate
  - SaveValues
  - ShowFilter

- **Phase 4B (Medium Priority Field Properties - Batch 1)**:
  - AssistEdit
  - ColumnSpan
  - DrillDown
  - HideValue
  - Importance

- **Phase 5 (Critical Expression Support)**:
  - DATABASE references (e.g., DATABASE::Customer)

### Next Steps

1. **Phase 6 (Remaining Medium and Low Priority Properties)**
   - Implement properties in small batches (5-8 at a time), creating appropriate test cases for each batch to ensure they parse correctly.

2. **Remaining Critical Priority Items**
   - ✅ Implement SourceTableView property with support for SORTING and WHERE clauses
   - ✅ Add support for separator action elements
   - ✅ Add support for DATABASE references
   - Fix page-level trigger declarations
   - Add support for remaining missing AL built-in functions and expression types
