// B7b-2 final scoped re-review: a property value with a leading prefix AND a tail, `Visible = #if X Ok and #endif Ok #if Y or Ok #endif;` (an action's Visible). alc accepts every configuration; the parser ERRORed over the tail until item 62's fix (docs/deferred-work.md item 62). Item 62's fix adds an action's Enabled with a tail that has an #else arm, and a page field's Editable/Visible/Enabled over a Boolean variable, which accept binary values too. A table field's Editable/Enabled/MinValue rejects a binary value (AL0104), so it is not a host here
// expect: * accept
// source: B7b-2 final scoped re-review, 2026-10-22 (reviewer probe scratchpad alc3/prop-prefix-tail.al), alc 18.0.41 four-way probe; extended 2026-10-25 (item 62 fix, Task 3)
page 50102 PG
{
    layout
    {
        area(Content)
        {
            field(F; Ok)
            {
                Editable =
#if X
                    Ok and
#endif
                    Ok
#if Y
                    or Ok
#endif
                    ;
                Visible =
#if X
                    Ok and
#endif
                    Ok
#if Y
                    or Ok
#endif
                    ;
                Enabled =
#if X
                    Ok and
#endif
                    Ok
#if Y
                    or Ok
#endif
                    ;
            }
        }
    }
    actions
    {
        area(Processing)
        {
            action(A1)
            {
                Visible =
#if X
                    Ok and
#endif
                    Ok
#if Y
                    or Ok
#endif
                    ;
                trigger OnAction()
                begin
                end;
            }
            action(A2)
            {
                Enabled =
#if X
                    Ok and
#endif
                    Ok
#if Y
                    or Ok
#else
                    and Ok
#endif
                    ;
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        Ok: Boolean;
}
