# VS Code AL Extension Sync Report

Generated: 2026-02-10 01:54:38
VS Code AL Extension: v17.0.2107262

## Executive Summary

This report compares the VS Code AL extension data with the tree-sitter grammar
to identify gaps and potential improvements.

> Items handled by generic mechanisms (attributes, ControlAddIn properties, triggers)
> or external scanner tokens are automatically classified as **false positives**.
> Only items that actually cause parse failures in production files are listed as missing.

| Data Source | Snippet Items | Grammar Items | Missing | False Positives | Coverage |
|-------------|---------------|---------------|---------|-----------------|----------|
| Keywords (tmlanguage) | 308 | 669 | 0 | 7 | 100.0% |
| Properties (snippets) | 55 | 908 | 0 | 17 | 100.0% |
| Triggers (snippets) | 7 | 24 | 0 | 1 | 100.0% |

## 1. Missing Keywords (from tmlanguage)

*All keywords are covered in grammar (or classified as false positives).*

## 2. Missing Properties (from snippets)

*All properties are covered in grammar (or classified as false positives).*

## 3. Missing Triggers (from snippets)

*All triggers are covered in grammar (or classified as false positives).*

## 3a. False Positives (handled by generic mechanisms)

These items are flagged as 'missing' by the comparison but work correctly
via generic grammar rules, external scanner tokens, or are not used in production.

### Keywords

| Keyword | Reason |
|---------|--------|
| `downto` | Handled by external scanner token `for_downto_keyword` (grammar.js externals) |
| `program` | Legacy C/AL keyword not used in modern AL (Business Central) |
| `runonclient` | Attribute handled by generic `attribute_item` rule: [RunOnClient] |
| `securityfiltering` | Attribute handled by generic `attribute_item` rule: [SecurityFiltering(...)] |
| `suppressdispose` | Attribute handled by generic `attribute_item` rule: [SuppressDispose] (not used in production) |
| `to` | Handled by external scanner token `for_to_keyword` (grammar.js externals) |
| `withevents` | Attribute handled by generic `attribute_item` rule: [WithEvents] |

### Properties

| Property | Reason |
|----------|--------|
| `definitionfile` | Not used as a property in any production file (only as variable name) |
| `extensible` | Already defined in grammar.js as `extensible_property` |
| `horizontalshrink` | Handled by generic `controladdin_property` rule (any identifier = boolean) |
| `horizontalstretch` | Handled by generic `controladdin_property` rule (any identifier = boolean) |
| `maximumheight` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `maximumwidth` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `minimumheight` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `minimumwidth` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `profiledescription` | Already defined in grammar.js as `profile_description_property2` |
| `recreatescript` | Handled by generic `controladdin_property` rule (any identifier = string) |
| `refreshscript` | Handled by generic `controladdin_property` rule (any identifier = string) |
| `requestedheight` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `requestedwidth` | Handled by generic `controladdin_property` rule (any identifier = integer) |
| `startupscript` | Handled by generic `controladdin_property` rule (any identifier = string) |
| `stylesheets` | Handled by generic `controladdin_property` rule (any identifier = string) |
| `verticalshrink` | Handled by generic `controladdin_property` rule (any identifier = boolean) |
| `verticalstretch` | Handled by generic `controladdin_property` rule (any identifier = boolean) |

### Triggers

| Trigger | Reason |
|---------|--------|
| `onbeforeopen` | Handled by generic `trigger_declaration` rule (accepts any identifier as trigger name) |

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

3. **Add to false positives list**: If verified as working, add to `FALSE_POSITIVE_*` in `config.py`

### Potential Improvements

1. **Verify enum value coverage** against grammar choice() rules if strict validation needed

---
*Report generated by keyword-sync tools*
