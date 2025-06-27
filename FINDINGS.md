# Grammar Analysis Findings & Prioritized Action Plan

This document outlines opportunities for consolidation and improvement within the `grammar.js` file, followed by a prioritized plan for implementation.

## Prioritized Action Plan

The following is a prioritized list for implementing the proposed changes, ordered from most critical and highest impact to least critical.

### Priority 1: Critical Fixes & Foundational Cleanup
These are the most important changes to address first as they either fix direct conflicts or establish foundational patterns that will be used in subsequent steps.

1.  **Fix Filter Expression Duplication (Finding 3):** This is the highest priority because it resolves a name collision, which can cause parsing ambiguities and makes the grammar difficult to maintain. Renaming the two `filter_expression` rules to `source_view_filter_expression` and `simple_filter_expression` is a critical fix.
2.  **Remove Redundant `ident()` function (Finding 4):** This is a very low-effort task that immediately cleans up the code by removing an unused function.
3.  **Create Centralized `_boolean_value` Rule (Finding 8):** This is a high-impact, low-effort change. Establishing a single `_boolean_value` rule will immediately improve consistency and is a simple, foundational step for standardizing property definitions.
4.  **Consolidate Object References (Finding 1):** Similar to the boolean rule, creating a single `_object_reference` rule is a high-impact, low-effort task that significantly reduces redundancy for a very common pattern.

### Priority 2: Major Consolidations
These changes involve larger-scale refactoring that will significantly simplify the grammar by removing duplicate structures.

5.  **Consolidate Permission Definitions (Finding 2):** This is a major cleanup. Unifying the `Permissions` and `AccessByPermission` rules into a single `_permission_definition` will eliminate a significant amount of redundant code and simplify the grammar's logic for handling permissions.
6.  **Standardize Keyword Usage with `kw()` (Finding 6):** This is a widespread but important change. Consistently using the `kw()` helper function will make the grammar more robust, readable, and easier to maintain. This should be done as a focused effort across the entire file.

### Priority 3: Further Refinements
These are valuable consolidations that can be addressed after the more critical issues are resolved.

7.  **Consolidate `About` Properties (Finding 7):** This is a targeted cleanup that follows the same consolidation principles. Merging the `page_about_..._ml_property` rules into more generic `about_..._ml_property` rules is a good final step for property consolidation.
8.  **Generalize Property Templates (Finding 5):** This is the most architectural change. Replacing specific templates (e.g., `_boolean_property_template`) with the more generic `_value_property_template` is a good practice for long-term maintainability but is less urgent than the other items. It can be done last to refine the overall structure.

---

## Original Findings

### 1. Object Reference Consolidation
**Observation**: Several properties that refer to AL objects (like Tables or Pages) share a common value pattern but use different or inline rule definitions.
**Resolution**: Create a new, centralized rule `_object_reference` and refactor all properties that refer to an object to use this single rule.

### 2. Permission Definition Consolidation
**Observation**: The grammar defines permission structures in two different places for `Permissions` and `AccessByPermission` properties, despite being structurally identical.
**Resolution**: Create a single, unified rule named `_permission_definition` and refactor both properties to use this new, consolidated rule.

### 3. Filter Expression Duplication
**Observation**: The name `filter_expression` is used for two different rule definitions, creating a potential conflict.
**Resolution**: Rename the two rules to `source_view_filter_expression` and `simple_filter_expression` to reflect their specific contexts.

### 4. Redundant `ident()` function
**Observation**: The grammar defines a helper function `ident()` that is not used anywhere.
**Resolution**: Remove the `ident()` function.

### 5. Overly specific property templates
**Observation**: The grammar uses overly specific templates like `_boolean_property_template`, leading to a proliferation of similar rules.
**Resolution**: Use the generic `_value_property_template` more broadly to replace these specific templates.

### 6. Inconsistent use of `kw()` for keywords
**Observation**: The `kw()` helper function for case-insensitive keywords is not used consistently.
**Resolution**: All keywords should be defined using the `kw()` function.

### 7. Consolidation of `About` properties
**Observation**: `page_about_text_ml_property` and `page_about_title_ml_property` are separate from their consolidated non-ML counterparts.
**Resolution**: Consolidate these ML properties into more generic `about_text_ml_property` and `about_title_ml_property` rules.

### 8. Lack of a centralized `_boolean_value` rule
**Observation**: Many properties that accept a boolean value define the choice of `true` or `false` inline.
**Resolution**: Create a centralized `_boolean_value` rule (`choice(kw('true'), kw('false'))`) and use it in all boolean properties.
