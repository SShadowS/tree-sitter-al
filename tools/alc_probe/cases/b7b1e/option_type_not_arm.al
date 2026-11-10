// B7b-1e (deferred item 46, the `not` arm before a comma-led member): an Option type whose first member is the word `not` inside a group, then a comma-led member (X=1 `Option not,B`), and the same with a name arm (`Foo`). alc accepts both configurations.
// expect: * accept
// source: B7b-1e probe, measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        V1: Option
#if X
            not
#endif
            ,B;
        V2: Option
#if X
            Foo
#endif
            ,B;
}
