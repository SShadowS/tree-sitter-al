// A comma-less `Visible = #if X and #endif Ok;`: the parser reads it clean as a two-member option list (`and`, `Ok`); alc rejects X=1 (`Visible = and Ok;`), so the tree over-accepts (docs/deferred-work.md item 65)
// expect: !X accept
// expect: X reject(AL0224)
// source: item 61's fix, 2026-10-25 (task-2 scratch probe commaless-and.al), alc 18.0.41 four-way probe
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
                    and
#endif
                    Ok;
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        Ok: Boolean;
}
