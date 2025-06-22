# Complex Module Parsing Failure Patterns Analysis

## Overview
Analysis of 10+ error files from BC.History focusing on Integration, AI, and Workflow modules reveals several unique parsing failure patterns specific to these complex modules.

## 1. Integration Module Patterns

### TableType = CRM Pattern
**Files Affected:** All CDS* and CRM* tables in Integration/D365Sales
**Error Pattern:**
```al
table 5371 "CDS Available Virtual Table"
{
    ExternalName = 'dyn365bc_businesscentralentity';
    TableType = CRM;  // ERROR: 'CRM' not recognized as valid table type
    Description = 'Contains available Business Central tables in Dataverse.';
```

**Issue:** The parser doesn't recognize `CRM` as a valid value for the `TableType` property. This is specific to Dataverse/CRM integration tables.

### ExternalAccess Property
**Files Affected:** Integration tables with external field mappings
**Error Pattern:**
```al
field(1; mserp_businesscentralentityId; GUID)
{
    ExternalName = 'dyn365bc_businesscentralentityid';
    ExternalType = 'Uniqueidentifier';
    ExternalAccess = Insert;  // ERROR: ExternalAccess property not recognized
```

**Issue:** The `ExternalAccess` property with values like `Insert` is not handled by the parser.

## 2. AI Module Patterns

### Style Property in PromptDialog Pages
**Files Affected:** BankAccRecAIProposal.Page.al, TransToGLAccAIProposal.Page.al
**Error Pattern:**
```al
field("Warning Text"; WarningTxt)
{
    Caption = '';
    ShowCaption = false;
    Editable = false;
    Style = Ambiguous;  // ERROR: 'Style' property not recognized
    MultiLine = true;
```

**Issue:** The `Style` property (distinct from `StyleExpr`) is not recognized in field declarations within PromptDialog page types.

### Interface Access Modifier
**Files Affected:** All *.Interface.al files in AI modules
**Error Pattern:**
```al
interface "Image Analysis Provider"
{
    Access = Internal;  // ERROR: Access property not recognized in interfaces
```

**Issue:** The `Access` property is not recognized within interface declarations.

### Interface Procedure Signatures
**Files Affected:** AI interface files
**Error Pattern:**
```al
procedure IsLanguageSupported(AnalysisTypes: List of [Enum "Image Analysis Type"]; Language: Integer): Boolean
// Missing semicolon causes parsing to fail on complex parameter types
```

**Issue:** Interface procedures with complex parameter types (e.g., `List of [Enum "Type"]`) without semicolons cause parsing failures.

## 3. Workflow Module Patterns

### IndentationColumn Property
**Files Affected:** WorkflowSteps.Page.al, WorkflowSubpage.Page.al, WorkflowTemplates.Page.al
**Error Pattern:**
```al
repeater(Group)
{
    IndentationColumn = Rec.Indent;  // ERROR: Parser expects different syntax
    IndentationControls = "Event Description";
```

**Issue:** The `IndentationColumn` property syntax with direct field reference is not properly parsed.

### OrderBy Property in Queries
**Files Affected:** WorkflowDefinition.Query.al, WorkflowInstance.Query.al
**Error Pattern:**
```al
query 1502 "Workflow Definition"
{
    Caption = 'Workflow Definition';
    OrderBy = ascending(Sequence_No);  // ERROR: OrderBy not recognized
```

**Issue:** The `OrderBy` property with sorting functions is not recognized in query objects.

### Complex Variable Declarations
**Files Affected:** Various workflow and AI codeunits
**Error Pattern:**
```al
var
    ConfigLine: Record "Config. Line" { temporary = true; };  // ERROR: inline modifiers
```

**Issue:** Variable declarations with inline property modifiers cause parsing failures.

## 4. Cross-Module Patterns

### Multi-Language/Conditional Compilation
**Files Affected:** FlowUserEnvSelection.Page.al
**Error Pattern:**
```al
#if CLEAN23
page 6402 "Flow User Env. Selection"
{
    // ... page content
}
#endif
```

**Issue:** Preprocessor directives for conditional compilation are not supported.

### Complex Attribute Lists
**Files Affected:** Various AI and integration codeunits
**Error Pattern:**
```al
[EventSubscriber(ObjectType::Codeunit, Codeunit::"ML Prediction Management", 'OnBeforePredict', '', false, false)]
local procedure OnBeforePredict(var Handled: Boolean; var Model: Text; var ConfidenceJsonAsText: Text; var FeatureJsonAsText: Text)
```

**Issue:** Long attribute argument lists sometimes cause parsing issues when line breaks occur within the attribute.

## Summary

The complex modules (Integration, AI, Workflow) introduce several unique parsing challenges:

1. **External Integration Properties**: `TableType = CRM`, `ExternalAccess`, external schema mappings
2. **AI-Specific UI Properties**: `Style` (not `StyleExpr`), PromptDialog-specific properties
3. **Interface Syntax**: `Access` modifiers, complex procedure signatures without semicolons
4. **Workflow UI Properties**: `IndentationColumn`, `IndentationControls` with specific syntax
5. **Query-Specific Properties**: `OrderBy` with functions
6. **Advanced Language Features**: Conditional compilation, inline variable modifiers

These patterns suggest that complex modules use more advanced AL language features that require specific grammar support, particularly around:
- External system integration
- Modern UI patterns (PromptDialog, tree views)
- Interface definitions
- Query objects
- Conditional compilation