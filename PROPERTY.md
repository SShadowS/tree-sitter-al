# PROPERTY.md - Complete Properties Audit Plan

This document provides a step-by-step plan for auditing all properties from the Microsoft Business Central documentation to ensure complete coverage in our tree-sitter grammar.

## Overview

We need to verify that every property listed in the Microsoft Business Central documentation is properly implemented in our grammar, either as universal properties or in specific object property lists:

- [Table Properties](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/properties/devenv-table-property-overview) - Table, Table Field, and Table Extension properties
- [Page Properties](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/properties/devenv-page-property-overview) - Page, Page Field, and Page Extension properties
- [Report Properties](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/properties/devenv-report-property-overview) - Report, Report Field, and Report Extension properties

## Core Principles

**CRITICAL RULE: PRESERVE UNIVERSAL PROPERTIES**
- ❌ **NEVER move properties OUT of `_universal_properties`** if they are already there
- ✅ **ALWAYS favor placing properties in `_universal_properties`** when in doubt about placement
- ✅ **Only use object-specific lists for truly exclusive properties** (rare cases)
- ✅ **Maintain backward compatibility** by preserving existing universal property definitions

This principle ensures maximum flexibility, prevents breaking changes, and follows the DRY (Don't Repeat Yourself) architecture already established in the grammar.

## Audit Process Steps

### Phase 1: Documentation Analysis and Preparation

#### Step 1.1: Extract All Properties from Documentation
From the Microsoft documentation, extract all properties that apply to:

**Table-Related Properties:**
- Table objects
- Table fields  
- Table extensions
- Table keys

**Page-Related Properties:**
- Page objects
- Page fields
- Page extensions
- Page actions
- Page groups
- Page parts
- Page views

**Report-Related Properties:**
- Report objects
- Report fields
- Report extensions
- Report data items
- Report columns
- Report layouts

Create a comprehensive list with the following information for each property:
- Property name
- Whether it's extensible (True/False)
- Which object types it applies to
- Expected value types/patterns

#### Step 1.2: Create Reference Checklist
Create a structured checklist with columns:
- [ ] Property Name
- [ ] Object Types (Table/Table Field/Table Key/Table Extension)  
- [ ] Extensible (Y/N)
- [ ] Grammar Status (Found/Missing/Partial)
- [ ] Grammar Location (Universal/_table_properties/etc.)
- [ ] Test Coverage (Y/N)
- [ ] Notes

### Phase 2: Grammar Analysis

#### Step 2.1: Search Current Grammar Implementation
For each property in the list, search the grammar.js file to determine:

1. **Property Definition Status:**
   - Search for property rule definition (e.g., `access_property`, `caption_property`)
   - Check if using `kw()` function for case-insensitive matching
   - Verify proper value type handling

2. **Property Inclusion Status:**
   - Check if included in `_universal_properties`
   - Check if included in `_table_properties` 
   - Check if included in `_field_properties`
   - Check if included in any other relevant property lists

3. **Implementation Quality:**
   - Proper use of `_value_property_template` or appropriate pattern
   - Case-insensitive keyword handling
   - Correct value type choices
   - Field wrappers where appropriate

#### Step 2.2: Identify Gaps and Issues
For each property, categorize as:
- ✅ **Complete**: Property defined and properly included in all relevant contexts
- ⚠️ **Partial**: Property defined but missing from some contexts or has implementation issues
- ❌ **Missing**: Property not defined in grammar
- 🔍 **Verify**: Property exists but needs verification of completeness

**CRITICAL RULE**: If a property is found in `_universal_properties`, mark it as ✅ **Complete** regardless of object-specific placement. NEVER suggest moving it out of universal.

### Phase 3: Property-by-Property Audit

#### Step 3.1: Universal Properties Verification
For properties marked as applying to multiple object types, verify they are in `_universal_properties`:

**Expected Universal Properties (from both Table and Page documentation):**
- Access
- Caption (extensible)
- CaptionML (extensible) 
- Description (extensible)
- ObsoleteReason
- ObsoleteState
- ObsoleteTag
- ToolTip (extensible)
- ToolTipML (extensible)
- AccessByPermission
- ApplicationArea (extensible)
- AutoFormatExpression
- AutoFormatType
- BlankNumbers
- BlankZero (extensible)
- CharAllowed
- ClosingDates (extensible)
- DateFormula
- DecimalPlaces
- Editable
- Enabled
- ExtendedDatatype
- HideValue (extensible)
- InherentEntitlements
- InherentPermissions
- LookupPageId (extensible)
- MaxValue
- MinValue
- NotBlank
- Numeric
- OptionCaption (extensible)
- OptionCaptionML (extensible)
- Permissions
- SignDisplacement
- TableRelation (extensible)
- ValuesAllowed
- Visible (extensible)
- AdditionalSearchTerms (extensible)
- AdditionalSearchTermsML (extensible)
- AutoCalcField
- DataAccessIntent
- TransactionType
- UsageCategory
- UseRequestPage
- And others marked as applying to multiple object types

#### Step 3.2: Table-Specific Properties Verification
Verify table-only properties are properly categorized:

**Expected Table-Only Properties:**
- ColumnStoreIndex
- CompressionType
- DataPerCompany
- DataCaptionFields (extensible)
- DrillDownPageId (extensible)
- Extensible
- ExternalName
- ExternalSchema
- InherentEntitlements
- InherentPermissions
- LinkedInTransaction
- LinkedObject
- LookupPageId (extensible)
- MovedFrom
- MovedTo
- PasteIsValid
- Permissions
- ReplicateData
- TableType

#### Step 3.3: Table Field Properties Verification
Verify field-specific properties are in appropriate field property lists:

**Key Field Properties to Verify:**
- AutoFormatExpression
- AutoFormatType
- AutoIncrement
- BlankNumbers
- BlankZero (extensible)
- CalcFormula
- CaptionClass (extensible)
- CharAllowed
- ClosingDates (extensible)
- Compressed
- DateFormula
- DecimalPlaces
- Editable
- ExtendedDatatype
- ExternalAccess
- ExternalName
- ExternalType
- FieldClass
- InitValue
- MaxValue
- MinValue
- NotBlank
- Numeric
- OptimizeForTextSearch
- OptionCaption (extensible)
- OptionCaptionML (extensible)
- OptionOrdinalValues
- SignDisplacement
- SqlDataType
- SqlTimestamp
- TableRelation (extensible)
- TestTableRelation
- ValidateTableRelation
- ValuesAllowed
- And others...

#### Step 3.4: Table Key Properties Verification
Verify key-specific properties:

**Key Properties to Verify:**
- Clustered
- Description (extensible)
- Enabled
- IncludedFields
- MaintainSiftIndex
- MaintainSqlIndex
- ObsoleteReason
- ObsoleteState
- ObsoleteTag
- SqlIndex
- SumIndexFields
- Unique

#### Step 3.5: Page-Specific Properties Verification
Verify page-only properties are properly categorized:

**Expected Page-Only Properties:**
- AboutText (extensible)
- AboutTextML (extensible)  
- AboutTitle (extensible)
- AboutTitleML (extensible)
- AdditionalSearchTerms (extensible)
- AdditionalSearchTermsML (extensible)
- AnalysisModeEnabled
- AutoSplitKey
- CardPageId (extensible)
- ChangeTrackingAllowed
- ContextSensitiveHelpPage (extensible)
- DataAccessIntent
- DataCaptionExpression (extensible)
- DelayedInsert
- DeleteAllowed (extensible)
- EntityCaption
- EntityCaptionML
- EntityName
- EntitySetCaption
- EntitySetCaptionML
- EntitySetName
- Extensible
- HelpLink
- InsertAllowed (extensible)
- InstructionalText (extensible)
- InstructionalTextML (extensible)
- IsPreview
- LinksAllowed
- ModifyAllowed (extensible)
- MultipleNewLines
- ODataKeyFields
- PageType
- PopulateAllFields
- PromotedActionCategories (extensible)
- PromotedActionCategoriesML (extensible)
- PromptMode
- QueryCategory
- RefreshOnActivate
- SaveValues
- ShowFilter
- SourceTable
- SourceTableTemporary
- UsageCategory

#### Step 3.6: Page Field Properties Verification
Verify page field-specific properties:

**Key Page Field Properties to Verify:**
- AssistEdit (extensible)
- CaptionClass (extensible)
- ColumnSpan
- DrillDown
- DrillDownPageId (extensible)
- Importance (extensible)
- Lookup
- MultiLine
- NavigationPageId
- ODataEDMType (extensible)
- QuickEntry (extensible)
- RowSpan
- ShowCaption (extensible)
- ShowMandatory (extensible)
- Style (extensible)
- StyleExpr (extensible)
- Title

#### Step 3.7: Page Action Properties Verification
Verify action-specific properties:

**Key Action Properties to Verify:**
- Ellipsis
- FlowCaption
- FlowEnvironmentId
- FlowId
- FlowTemplateCategoryName
- FlowTemplateId
- Gesture
- Image
- InFooterBar (extensible)
- PromotedCategory (extensible)
- PromotedIsBig (extensible)
- PromotedOnly (extensible)
- RunObject
- RunPageLink
- RunPageMode
- RunPageOnRec
- RunPageView
- ShortcutKey (extensible)
- ShowAs (extensible)

#### Step 3.8: Page Group Properties Verification
Verify group-specific properties:

**Key Group Properties to Verify:**
- CuegroupLayout
- FileUploadAction
- FileUploadRowAction
- FreezeColumn (extensible)
- GridLayout
- IndentationColumn (extensible)
- IndentationControls (extensible)
- ShowAsTree
- ShowCaption (extensible)
- TreeInitialState (extensible)

#### Step 3.9: Page Part Properties Verification
Verify part-specific properties:

**Key Part Properties to Verify:**
- EntityName
- EntitySetName
- Multiplicity
- Provider
- SubPageLink
- SubPageView
- UpdatePropagation

#### Step 3.10: Page Custom Action Properties Verification
Verify custom action-specific properties:

**Key Custom Action Properties to Verify:**
- AllowedFileExtensions (extensible)
- AllowMultipleFiles (extensible)
- CustomActionType
- FlowCaption
- FlowEnvironmentId
- FlowId
- FlowTemplateCategoryName
- FlowTemplateId

#### Step 3.11: Page View Properties Verification
Verify view-specific properties:

**Key View Properties to Verify:**
- Filters
- OrderBy
- SharedLayout

#### Step 3.12: Report-Specific Properties Verification
Verify report-only properties are properly categorized:

**Expected Report-Only Properties:**
- AllowScheduling
- DefaultLayout
- DefaultRenderingLayout
- EnableExternalAssemblies
- EnableExternalImages
- EnableHyperlinks
- ExcelLayout (extensible)
- ExcelLayoutMultipleDataSheets
- ExecutionTimeout
- FormatRegion
- MaximumDatasetSize
- MaximumDocumentCount
- PaperSourceDefaultPage
- PaperSourceFirstPage
- PaperSourceLastPage
- PdfFontEmbedding
- PreviewMode
- ProcessingOnly
- RDLCLayout (extensible)
- ShowPrintStatus
- UseSystemPrinter
- WordLayout (extensible)
- WordMergeDataItem

#### Step 3.13: Report Data Item Properties Verification
Verify data item-specific properties:

**Key Data Item Properties to Verify:**
- CalcFields
- DataItemLinkReference
- DataItemTableView
- Description (extensible)
- MaxIteration
- ObsoleteReason
- ObsoleteState
- ObsoleteTag
- PrintOnlyIfDetail
- RequestFilterFields
- RequestFilterHeading
- RequestFilterHeadingML

#### Step 3.14: Report Column Properties Verification
Verify column-specific properties:

**Key Column Properties to Verify:**
- AutoCalcField
- AutoFormatExpression
- AutoFormatType
- Caption (extensible)
- CaptionML (extensible)
- DecimalPlaces
- Description (extensible)
- IncludeCaption
- ObsoleteReason
- ObsoleteState
- ObsoleteTag
- OptionCaption (extensible)
- OptionCaptionML (extensible)

#### Step 3.15: Report Layout Properties Verification
Verify layout-specific properties:

**Key Layout Properties to Verify:**
- Caption (extensible)
- CaptionML (extensible)
- ExcelLayoutMultipleDataSheets
- LayoutFile
- MimeType
- ObsoleteReason
- ObsoleteState
- ObsoleteTag
- Summary
- SummaryML

### Phase 4: Implementation and Testing

#### Step 4.0: Property Placement Guidelines (CRITICAL)

**NEVER MOVE PROPERTIES OUT OF UNIVERSAL DEFINITION**
- If a property is already in `_universal_properties`, NEVER move it to object-specific lists
- This maintains backward compatibility and avoids breaking existing functionality
- Universal properties can be used across multiple object types, providing maximum flexibility

**FAVOR UNIVERSAL PLACEMENT**
- When in doubt about property placement, always favor `_universal_properties`
- Only place properties in object-specific lists if they are truly exclusive to that object type
- Check Microsoft documentation to verify if property applies to multiple object types
- If a property could reasonably be used in multiple contexts, place it in universal

**Implementation Priority:**
1. ✅ **Preserve existing universal properties** - Never remove or relocate
2. ✅ **Add new properties to universal when possible** - Check documentation for multi-object usage
3. ✅ **Only use object-specific lists for truly exclusive properties** - Rare cases only
4. ✅ **Document placement decisions** - Note reasoning for object-specific placement

#### Step 4.1: Add Missing Properties
For each missing property:

1. **Define the Property Rule:**
   ```javascript
   property_name_property: $ => _value_property_template(
     kw('PropertyName'),
     $.appropriate_value_type
   ),
   ```

2. **Add to Appropriate Property Lists:**
   - Add to `_universal_properties` if multi-object
   - Add to specific lists (`_table_properties`, `_field_properties`, etc.) if object-specific

3. **Create Test Cases:**
   - Add tests in `test/corpus/` covering the property in relevant contexts
   - Test with different value types and case variations

#### Step 4.2: Fix Partial Implementations
For properties with issues:

1. **Fix Case Sensitivity:**
   - Replace `choice('Property', 'property', 'PROPERTY')` with `kw('Property')`
   
2. **Add Missing Context Inclusion:**
   - Add property to missing property lists
   
3. **Fix Value Type Handling:**
   - Ensure all valid value types are supported
   - Add proper field wrappers

#### Step 4.3: Validation and Testing
For each property added/fixed:

1. **Run Grammar Validation:**
   ```bash
   ./validate-grammar.sh
   ```

2. **Test Property in Context:**
   ```bash
   tree-sitter test -i "property_pattern"
   ```

3. **Create Comprehensive Tests:**
   - Test property in table context
   - Test property in field context (if applicable)
   - Test property in key context (if applicable)
   - Test with various value types
   - Test case insensitivity

### Phase 5: Documentation and Verification

#### Step 5.1: Update Documentation
- Update CLAUDE.md with any new property patterns discovered
- Document any implementation decisions or limitations

#### Step 5.2: Final Verification
1. **Run Full Test Suite:**
   ```bash
   tree-sitter generate && tree-sitter test
   ```

2. **Test Against Real BC Files:**
   ```bash
   ./validate-grammar.sh --full
   ```

3. **Verify No Regressions:**
   - Ensure all existing tests still pass
   - Check that parsing success rate hasn't decreased

#### Step 5.3: Create Summary Report
Document the audit results:
- Total properties audited
- Properties added
- Properties fixed  
- Properties with known limitations
- Test coverage improvements
- Overall grammar completeness status

## Detailed Property List from Documentation

Based on the Microsoft documentation, here are all the properties that need to be audited:

### Table Object Properties (Table Level)
1. Access
2. Caption (extensible)
3. CaptionML (extensible)
4. ColumnStoreIndex
5. CompressionType
6. DataCaptionFields (extensible)
7. DataPerCompany
8. Description (extensible)
9. DrillDownPageId (extensible)
10. Extensible
11. ExternalName
12. ExternalSchema
13. InherentEntitlements
14. InherentPermissions
15. LinkedInTransaction
16. LinkedObject
17. LookupPageId (extensible)
18. MovedFrom
19. MovedTo
20. ObsoleteReason
21. ObsoleteState
22. ObsoleteTag
23. PasteIsValid
24. Permissions
25. ReplicateData
26. TableType

### Field Properties
1. Access
2. AccessByPermission
3. AllowInCustomizations
4. AutoFormatExpression
5. AutoFormatType
6. AutoIncrement
7. BlankNumbers
8. BlankZero (extensible)
9. CalcFormula
10. Caption (extensible)
11. CaptionClass (extensible)
12. CaptionML (extensible)
13. CharAllowed
14. ClosingDates (extensible)
15. Compressed
16. DateFormula
17. DecimalPlaces
18. Description (extensible)
19. DrillDownPageId (extensible)
20. Editable
21. Enabled
22. ExtendedDatatype
23. ExternalAccess
24. ExternalName
25. ExternalType
26. FieldClass
27. InitValue
28. LookupPageId (extensible)
29. MaxValue
30. MinValue
31. MovedFrom
32. MovedTo
33. NotBlank
34. Numeric
35. ObsoleteReason
36. ObsoleteState
37. ObsoleteTag
38. OptimizeForTextSearch
39. OptionCaption (extensible)
40. OptionCaptionML (extensible)
41. OptionOrdinalValues
42. SignDisplacement
43. SqlDataType
44. SqlTimestamp
45. TableRelation (extensible)
46. TestTableRelation
47. ToolTip (extensible)
48. ToolTipML (extensible)
49. ValidateTableRelation
50. ValuesAllowed

### Table Key Properties
1. Clustered
2. Description (extensible)
3. Enabled
4. IncludedFields
5. MaintainSiftIndex
6. MaintainSqlIndex
7. ObsoleteReason
8. ObsoleteState
9. ObsoleteTag
10. SqlIndex
11. SumIndexFields
12. Unique

### Page Object Properties (Page Level)
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. AccessByPermission
6. AdditionalSearchTerms (extensible)
7. AdditionalSearchTermsML (extensible)
8. AnalysisModeEnabled
9. ApplicationArea (extensible)
10. AutoSplitKey
11. Caption (extensible)
12. CaptionML (extensible)
13. CardPageId (extensible)
14. ChangeTrackingAllowed
15. ContextSensitiveHelpPage (extensible)
16. DataAccessIntent
17. DataCaptionExpression (extensible)
18. DataCaptionFields (extensible)
19. DelayedInsert
20. DeleteAllowed (extensible)
21. Description (extensible)
22. Editable
23. EntityCaption
24. EntityCaptionML
25. EntityName
26. EntitySetCaption
27. EntitySetCaptionML
28. EntitySetName
29. Extensible
30. HelpLink
31. InherentEntitlements
32. InherentPermissions
33. InsertAllowed (extensible)
34. InstructionalText (extensible)
35. InstructionalTextML (extensible)
36. IsPreview
37. LinksAllowed
38. ModifyAllowed (extensible)
39. MultipleNewLines
40. ODataKeyFields
41. ObsoleteReason
42. ObsoleteState
43. ObsoleteTag
44. PageType
45. Permissions
46. PopulateAllFields
47. PromotedActionCategories (extensible)
48. PromotedActionCategoriesML (extensible)
49. PromptMode
50. QueryCategory
51. RefreshOnActivate
52. SaveValues
53. ShowFilter
54. SourceTable
55. SourceTableTemporary
56. UsageCategory

### Page Field Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. ApplicationArea (extensible)
6. AssistEdit (extensible)
7. AutoFormatExpression
8. AutoFormatType
9. BlankNumbers
10. BlankZero (extensible)
11. Caption (extensible)
12. CaptionClass (extensible)
13. CaptionML (extensible)
14. CharAllowed
15. ClosingDates (extensible)
16. ColumnSpan
17. DateFormula
18. DecimalPlaces
19. Description (extensible)
20. DrillDown
21. DrillDownPageId (extensible)
22. Editable
23. Enabled
24. ExtendedDatatype
25. HideValue (extensible)
26. Image
27. Importance (extensible)
28. InstructionalText (extensible)
29. InstructionalTextML (extensible)
30. Lookup
31. LookupPageId (extensible)
32. MaxValue
33. MinValue
34. MultiLine
35. NavigationPageId
36. NotBlank
37. Numeric
38. ObsoleteReason
39. ObsoleteState
40. ObsoleteTag
41. ODataEDMType (extensible)
42. OptionCaption (extensible)
43. OptionCaptionML (extensible)
44. QuickEntry (extensible)
45. RowSpan
46. ShowCaption (extensible)
47. ShowMandatory (extensible)
48. SignDisplacement
49. Style (extensible)
50. StyleExpr (extensible)
51. TableRelation (extensible)
52. Title
53. ToolTip (extensible)
54. ToolTipML (extensible)
55. ValuesAllowed
56. Visible (extensible)

### Page Action Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. AccessByPermission
6. ApplicationArea (extensible)
7. Caption (extensible)
8. CaptionML (extensible)
9. Description (extensible)
10. Ellipsis
11. Enabled
12. Gesture
13. Image
14. InFooterBar (extensible)
15. ObsoleteReason
16. ObsoleteState
17. ObsoleteTag
18. PromotedCategory (extensible)
19. PromotedIsBig (extensible)
20. PromotedOnly (extensible)
21. RunObject
22. RunPageLink
23. RunPageMode
24. RunPageOnRec
25. RunPageView
26. ShortcutKey (extensible)
27. ToolTip (extensible)
28. ToolTipML (extensible)
29. Visible (extensible)

### Page Action Group Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. Caption (extensible)
6. CaptionML (extensible)
7. Description (extensible)
8. Enabled
9. Image
10. ObsoleteReason
11. ObsoleteState
12. ObsoleteTag
13. ShowAs (extensible)
14. ToolTip (extensible)
15. ToolTipML (extensible)
16. Visible (extensible)

### Page Group Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. Caption (extensible)
6. CaptionML (extensible)
7. CuegroupLayout
8. Description (extensible)
9. Editable
10. Enabled
11. FileUploadAction
12. FileUploadRowAction
13. FreezeColumn (extensible)
14. GridLayout
15. IndentationColumn (extensible)
16. IndentationControls (extensible)
17. InstructionalText (extensible)
18. InstructionalTextML (extensible)
19. ObsoleteReason
20. ObsoleteState
21. ObsoleteTag
22. ShowAsTree
23. ShowCaption (extensible)
24. TreeInitialState (extensible)
25. Visible (extensible)

### Page Part Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. AccessByPermission
6. ApplicationArea (extensible)
7. Caption (extensible)
8. CaptionML (extensible)
9. Description (extensible)
10. Editable
11. Enabled
12. EntityName
13. EntitySetName
14. Multiplicity
15. ObsoleteReason
16. ObsoleteState
17. ObsoleteTag
18. Provider
19. ShowFilter
20. SubPageLink
21. SubPageView
22. ToolTip (extensible)
23. ToolTipML (extensible)
24. UpdatePropagation
25. Visible (extensible)

### Page Custom Action Properties
1. AboutText (extensible)
2. AboutTextML (extensible)
3. AboutTitle (extensible)
4. AboutTitleML (extensible)
5. AccessByPermission
6. AllowedFileExtensions (extensible)
7. AllowMultipleFiles (extensible)
8. ApplicationArea (extensible)
9. Caption (extensible)
10. CaptionML (extensible)
11. CustomActionType
12. Ellipsis
13. Enabled
14. FlowCaption
15. FlowEnvironmentId
16. FlowId
17. FlowTemplateCategoryName
18. FlowTemplateId
19. Gesture
20. ObsoleteReason
21. ObsoleteState
22. ObsoleteTag
23. ShortcutKey (extensible)
24. ToolTip (extensible)
25. ToolTipML (extensible)
26. Visible (extensible)

### Page View Properties
1. Caption (extensible)
2. CaptionML (extensible)
3. Filters
4. ObsoleteReason
5. ObsoleteState
6. ObsoleteTag
7. OrderBy
8. SharedLayout
9. Visible (extensible)

### Page Label Properties
1. ApplicationArea (extensible)
2. Caption (extensible)
3. CaptionClass (extensible)
4. CaptionML (extensible)
5. ColumnSpan
6. Description (extensible)
7. Editable
8. Enabled
9. HideValue (extensible)
10. Importance (extensible)
11. MultiLine
12. ObsoleteReason
13. ObsoleteState
14. ObsoleteTag
15. RowSpan
16. ShowCaption (extensible)
17. Style (extensible)
18. StyleExpr (extensible)
19. ToolTip (extensible)
20. ToolTipML (extensible)
21. Visible (extensible)

### Report Object Properties (Report Level)
1. AccessByPermission
2. AdditionalSearchTerms (extensible)
3. AdditionalSearchTermsML (extensible)
4. AllowScheduling
5. ApplicationArea (extensible)
6. Caption (extensible)
7. CaptionML (extensible)
8. DataAccessIntent
9. DefaultLayout
10. DefaultRenderingLayout
11. Description (extensible)
12. EnableExternalAssemblies
13. EnableExternalImages
14. EnableHyperlinks
15. ExcelLayout (extensible)
16. ExcelLayoutMultipleDataSheets
17. ExecutionTimeout
18. Extensible
19. FormatRegion
20. InherentEntitlements
21. InherentPermissions
22. MaximumDatasetSize
23. MaximumDocumentCount
24. ObsoleteReason
25. ObsoleteState
26. ObsoleteTag
27. PaperSourceDefaultPage
28. PaperSourceFirstPage
29. PaperSourceLastPage
30. PdfFontEmbedding
31. Permissions
32. PreviewMode
33. ProcessingOnly
34. RDLCLayout (extensible)
35. ShowPrintStatus
36. ToolTip (extensible)
37. TransactionType
38. UsageCategory
39. UseRequestPage
40. UseSystemPrinter
41. WordLayout (extensible)
42. WordMergeDataItem

### Report Data Item Properties
1. CalcFields
2. DataItemLinkReference
3. DataItemTableView
4. Description (extensible)
5. MaxIteration
6. ObsoleteReason
7. ObsoleteState
8. ObsoleteTag
9. PrintOnlyIfDetail
10. RequestFilterFields
11. RequestFilterHeading
12. RequestFilterHeadingML

### Report Column Properties
1. AutoCalcField
2. AutoFormatExpression
3. AutoFormatType
4. Caption (extensible)
5. CaptionML (extensible)
6. DecimalPlaces
7. Description (extensible)
8. IncludeCaption
9. ObsoleteReason
10. ObsoleteState
11. ObsoleteTag
12. OptionCaption (extensible)
13. OptionCaptionML (extensible)

### Report Layout Properties
1. Caption (extensible)
2. CaptionML (extensible)
3. ExcelLayoutMultipleDataSheets
4. LayoutFile
5. MimeType
6. ObsoleteReason
7. ObsoleteState
8. ObsoleteTag
9. Summary
10. SummaryML

## Implementation Commands

```bash
# Start audit process
cd /mnt/u/git/tree-sitter-al

# Search for existing property implementations
rg "property:" grammar.js | sort

# Check property list inclusions
rg "_universal_properties\|_table_properties\|_field_properties" grammar.js

# Validate after changes
./validate-grammar.sh

# Test specific property patterns
tree-sitter test -i "property_name"

# Update test expectations if needed
tree-sitter test -u
```

## Success Criteria

The audit is complete when:
- ✅ All 400+ properties from the Microsoft documentation are accounted for (88 table + 237 page + 67 report properties)
- ✅ Each property is properly categorized (universal vs object-specific) **WITHOUT moving any existing universal properties**
- ✅ All properties use case-insensitive `kw()` functions
- ✅ All properties have appropriate value type handling
- ✅ Test coverage exists for all properties in relevant contexts
- ✅ Grammar validation passes without errors
- ✅ No regressions in existing functionality
- ✅ **No properties moved OUT of `_universal_properties`** (critical requirement)
- ✅ **New properties favor universal placement** when applicable to multiple object types
- ✅ Documentation is updated with any findings or limitations

**Property Count Summary:**
- **Table Object Properties**: 26 properties
- **Table Field Properties**: 50 properties
- **Table Key Properties**: 12 properties
- **Page Object Properties**: 56 properties
- **Page Field Properties**: 56 properties
- **Page Action Properties**: 29 properties
- **Page Action Group Properties**: 16 properties
- **Page Group Properties**: 25 properties
- **Page Part Properties**: 25 properties
- **Page Custom Action Properties**: 26 properties
- **Page View Properties**: 9 properties
- **Page Label Properties**: 21 properties
- **Report Object Properties**: 42 properties
- **Report Data Item Properties**: 12 properties
- **Report Column Properties**: 13 properties
- **Report Layout Properties**: 10 properties

**Total Properties to Audit**: ~392 properties

This comprehensive audit will ensure our tree-sitter grammar has complete coverage of all Business Central table, page, and report properties as documented by Microsoft.