; ── "OnBeforeDeleteEvent subscribers missing IsTemporary guard" ─────────────────────────────
(
  ; The attribute_item and procedure must be adjacent siblings (Rust-style attributes)
  (attribute_item
    attribute: (attribute_content
      name: (identifier) @attr_name
      arguments: (attribute_arguments
        arguments: (expression_list
          (qualified_enum_value)               ; ObjectType::Table
          [(integer) (database_reference)]     ; Table ID or Database::"Table Name"
          [(string_literal) (identifier)] @event_name ; Event name (with or without quotes)
          (string_literal)                     ; Publisher object
          (boolean)                            ; Publisher function
          (boolean)))))                        ; Skip on missing
  .                                            ; Adjacent sibling operator
  (procedure
    name: (name) @proc_name
    (parameter_list
      (parameter
        parameter_name: (name) @rec_param)     ; var Rec: Record
      (parameter
        parameter_name: (name)))               ; RunTrigger: Boolean
    (var_section)?                             ; Optional var section
    (code_block                                ; BEGIN … END;
      (_) @first_statement                     ; Capture first statement (any type)
      .))                                      ; Ensure it's the first
  (#eq? @attr_name "EventSubscriber")          ; Match EventSubscriber attribute
  (#match? @event_name "OnBeforeDeleteEvent")  ; Match OnBeforeDeleteEvent (with or without quotes)
  (#not-match? @first_statement "IsTemporary"); First statement does NOT contain IsTemporary
)