; Harness-owned extraction queries. Not a shipped query file — this exists to
; pull a full semantic inventory, which the editor-facing queries do not do.

; --- object identity -------------------------------------------------------
; Every named node type in src/node-types.json whose `fields` includes
; `object_name` — see inventory.object_declaration_types(), which enumerates
; this same set programmatically so a future addition can be re-derived and
; diffed against this file instead of hand-audited.
;
; 13 types carry both a required object_id and object_name:
(table_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(codeunit_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(page_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(report_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(xmlport_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(query_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(enum_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(permissionset_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(enumextension_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(pageextension_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(permissionsetextension_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(reportextension_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object
(tableextension_declaration object_id: (integer) @object.id object_name: (_) @object.name) @object

; 6 types carry object_name only — these AL object kinds are never numbered
; (interfaces, control add-ins, entitlements, page customizations, profiles
; and profile extensions are referenced by name alone):
(controladdin_declaration object_name: (_) @object.name) @object
(entitlement_declaration object_name: (_) @object.name) @object
(interface_declaration object_name: (_) @object.name) @object
(pagecustomization_declaration object_name: (_) @object.name) @object
(profile_declaration object_name: (_) @object.name) @object
(profileextension_declaration object_name: (_) @object.name) @object

; preproc_split_declaration: the object header itself is fragmented across
; #if/#elif/#else branches (id/name can differ per branch), so node-types.json
; marks object_id `multiple: true, required: false` and object_name
; `multiple: true, required: true`. Capturing object_id here would either
; miss the interface-header branch (no id at all) or, worse, double-match
; this node against a second id-optional pattern and duplicate it in
; extract(). Capture object_name only; extract() reads object_id via
; child_by_field_name, which returns None exactly when a branch omits it.
(preproc_split_declaration object_name: (_) @object.name) @object

; --- properties --------------------------------------------------------------
(property name: (property_name) @property.name value: (_) @property.value) @property

; --- fields --------------------------------------------------------------------
(field_declaration id: (integer) @field.id name: (_) @field.name) @field

; --- procedures ------------------------------------------------------------
(procedure name: (_) @procedure.name) @procedure
(parameter name: (_) @parameter.name) @parameter

; --- triggers ----------------------------------------------------------------
(trigger_declaration name: (_) @trigger.name) @trigger

; --- enum values -------------------------------------------------------------
(enum_value_declaration value_id: (integer) @enum.id value_name: (_) @enum.name) @enum

; --- keys ----------------------------------------------------------------------
(key_declaration name: (_) @key.name fields: (field_list) @key.fields) @key

; --- variable declarations ----------------------------------------------------
(variable_declaration name: (_) @variable.name type: (_) @variable.type) @variable

; --- page layout: every control shape carries a `name` field -----------------
(page_field name: (_) @control.name) @control
(group_section name: (_) @control.name) @control
(repeater_section name: (_) @control.name) @control
(fixed_section name: (_) @control.name) @control
(grid_section name: (_) @control.name) @control
(cuegroup_section name: (_) @control.name) @control
(part_section name: (_) @control.name) @control
(systempart_section name: (_) @control.name) @control
(label_section name: (_) @control.name) @control

; --- page actions --------------------------------------------------------------
(action_declaration name: (_) @action.name) @action
(action_group_section name: (_) @action.name) @action
(actionref_declaration promoted_name: (_) @action.promoted_name action_name: (_) @action.action_name) @action
(systemaction_declaration name: (_) @action.name) @action
(separator_action name: (_) @action.name) @action
(customaction_declaration name: (_) @action.name) @action
(fileuploadaction_declaration name: (_) @action.name) @action
