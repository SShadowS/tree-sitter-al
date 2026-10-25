// A comma-less `Visible = #if X Foo #endif Ok;`: the parser reads it clean as a two-member option list (`Foo`, `Ok`); alc rejects X=1 (`Visible = Foo Ok;`), so the tree over-accepts (docs/deferred-work.md item 65)
// expect: !X accept
// expect: X reject(AL0104,AL0124)
// source: item 61's fix, 2026-10-25 (task-2 scratch probe commaless-foo.al), alc 18.0.41 four-way probe
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
                    Foo
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
        Foo: Boolean;
}
