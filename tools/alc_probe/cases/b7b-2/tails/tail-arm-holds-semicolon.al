// A property-value tail whose arms hold the property's `;`: `Visible = Ok #if Y or Ok; #else ; #endif` (an action's Visible). alc accepts both configurations; the parser ERRORs on main and after item 62's fix (docs/deferred-work.md item 39 shape 2, the property-value form of `;` inside continuation arms)
// expect: * accept
// source: small-correctness fixes Task 3 review minor, 2026-10-25, alc 18.0.41 four-way probe
page 50102 PG
{
    actions
    {
        area(Processing)
        {
            action(A1)
            {
                Visible = Ok
#if Y
                    or Ok;
#else
                    ;
#endif
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        Ok: Boolean;
}
