# VS Code AL Extension Sync Report

Generated: 2026-02-02 10:53:27
VS Code AL Extension: v17.0.2037090

## Executive Summary

This report compares the VS Code AL extension data with the tree-sitter grammar
to identify gaps and potential improvements.

> **Note**: Many 'missing' items are **false positives** because:
> - Keywords like `InDataSet`, `RunOnClient`, `SecurityFiltering` are **attributes** that work via the generic `attribute_item` rule
> - Keywords like `to`, `downto` are handled by **external scanner tokens** (`for_to_keyword`, `for_downto_keyword`)
> - ControlAddIn properties work via the generic `controladdin_property` rule (accepts any identifier)
> - Triggers like `OnBeforeOpen` work via generic trigger support
>
> Before adding items to the grammar, verify they actually cause parse failures in production files.

| Data Source | Snippet Items | Grammar Items | Missing | Coverage |
|-------------|---------------|---------------|---------|----------|
| Keywords (tmlanguage) | 308 | 668 | 8 | 97.4% |
| Properties (snippets) | 55 | 907 | 17 | 69.1% |
| Triggers (snippets) | 7 | 24 | 1 | 85.7% |

## 1. Missing Keywords (from tmlanguage)

Keywords defined in the TextMate syntax but not found in grammar.js.

### Control Flow

| Keyword | Special Handling |
|---------|------------------|
| `downto` | kw |
| `indataset` | kw |
| `program` | kw |
| `runonclient` | kw |
| `securityfiltering` | kw |
| `suppressdispose` | kw |
| `to` | kw |
| `withevents` | kw |

## 2. Missing Properties (from snippets)

Properties used in snippets but potentially not in grammar.js.

### High Priority (have enum values)

| Property | Enum Values | Sources |
|----------|-------------|---------|
| `extensible` | true, false | enum.json, page.json |
| `horizontalshrink` | true, false | controladdin.json |
| `horizontalstretch` | true, false | controladdin.json |
| `verticalshrink` | true, false | controladdin.json |
| `verticalstretch` | true, false | controladdin.json |

### Lower Priority (no enum values)

| Property | Example Value | Sources |
|----------|---------------|---------|
| `definitionfile` | '${2:DefinitionFilePath}' | page.json |
| `maximumheight` | 300 | controladdin.json |
| `maximumwidth` | 700 | controladdin.json |
| `minimumheight` | 300 | controladdin.json |
| `minimumwidth` | 700 | controladdin.json |
| `profiledescription` | '${4:Profile Description}' | profile.json |
| `recreatescript` | '${16:recreateScript.js}' | controladdin.json |
| `refreshscript` | '${17:refreshScript.js}' | controladdin.json |
| `requestedheight` | 300 | controladdin.json |
| `requestedwidth` | 700 | controladdin.json |
| `startupscript` | '${15:startupScript.js}' | controladdin.json |
| `stylesheets` | '${14:style.css}' | controladdin.json |

## 3. Missing Triggers (from snippets)

Triggers used in snippets but not found in grammar.js.

| Trigger Name |
|--------------|
| `onbeforeopen` |

## 4. Enum Value Reference

Complete list of enum values found in snippets for each property.
Use this to verify grammar covers all valid values.

### ApplicationArea

```
Advanced, All, Basic, Suite
```

### Assignable

```
false, true
```

### Clustered

```
false, true
```

### DataClassification

```
AccountData, CustomerContent, EndUserIdentifiableInformation, EndUserPseudonymousIdentifiers, OrganizationIdentifiableInformation, SystemMetadata, ToBeClassified
```

### Extensible

```
false, true
```

### HorizontalShrink

```
false, true
```

### HorizontalStretch

```
false, true
```

### PageType

```
API, Card, CardPart, ConfirmationDialog, Document, List, ListPart, ListPlus, NavigatePage, ReportPreview, ReportProcessingOnly, RoleCenter, StandardDialog, Worksheet, XmlPort
```

### PromptMode

```
Content, Generate, Prompt
```

### QueryType

```
API, Normal
```

### RoleType

```
Delegated, Local
```

### RunObject

```
Codeunit, Page, Report, XmlPort
```

### Type

```
Application, ApplicationScope, ConcurrentUserServicePlan, FlatRateServicePlan, Group, Implicit, PerUserServicePlan, Role
```

### UsageCategory

```
Administration, Documents, History, Lists, None, ReportsAndAnalysis, Tasks
```

### VerticalShrink

```
false, true
```

### VerticalStretch

```
false, true
```

### addlast

```
Brick, DropDown
```

### fieldgroup

```
Brick, DropDown
```

### systemaction

```
Attach, Cancel, Generate, Ok, Regenerate
```

## 5. Structural Elements Reference

### Section Types

```
actions, area, dataitem, dataset, fieldgroups, fields, group, keys, layout, rendering, repeater, requestpage
```

### Area Types

```
Content, Creation, Embedding, Factboxes, Prompt, PromptOptions, RoleCenter, Sections, SystemActions, content
```

### Keywords/Constructs

```
action, actionref, analysisview, column, customaction, event, field, key, part, procedure, systemaction, usercontrol, view
```

## 6. Recommended Actions

Based on the analysis, here are the recommended next steps:

### Before Adding Items

1. **Verify parse failures**: Check if the 'missing' item actually causes errors
   ```bash
   # Search for usage in production files
   grep -ri 'ItemName' ./BC.History/ | head -5
   # Parse a file that uses it
   tree-sitter parse file.al 2>&1 | grep ERROR
   ```

2. **Check generic rules**: Many items work via generic mechanisms:
   - `controladdin_property` - Any `PropertyName = value;` in ControlAddIn objects
   - `attribute_item` - Any `[AttributeName]` or `[AttributeName(args)]`
   - Generic trigger support - `trigger OnXxx() begin end;`

### Potential Improvements

1. **Review 8 'missing' keywords** - most are false positives (attributes, scanner tokens)
2. **Review 5 properties with enum values** - may need specific rules if values are validated
3. **Review 1 'missing' triggers** - likely work via generic trigger support
4. **Verify enum value coverage** against grammar choice() rules if strict validation needed

---
*Report generated by keyword-sync tools*
