// `OptionMembers = #if X not #endif ,B;`: an option-member arm that is the word `not`, then a comma-led member. alc accepts both configurations (X=1 `OptionMembers = not,B;`); the parser ERRORs on main and after item 61's fix (docs/deferred-work.md item 46, option-members). The same input with a name arm (`Foo`) ERRORs too
// expect: * accept
// source: small-correctness fixes Task 2 review minor, 2026-10-25, alc 18.0.41 four-way probe
table 50100 T
{
    fields
    {
        field(1; F; Option)
        {
            OptionMembers =
#if X
                not
#endif
                ,B;
        }
    }
}
