// B7b-2 final scoped re-review: a property value with a leading prefix AND a tail, `Visible = #if X Ok and #endif Ok #if Y or Ok #endif;` (an action's Visible: page Editable rejects binary values outright). alc accepts every configuration; the parser ERRORs over the tail (docs/deferred-work.md item 62)
// expect: * accept
// source: B7b-2 final scoped re-review, 2026-10-22 (reviewer probe scratchpad alc3/prop-prefix-tail.al), alc 18.0.41 four-way probe
page 50102 PG
{
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
        }
    }
    var
        Ok: Boolean;
}
