// Deferred item 23: a Permissions list whose `;` is inside the #if arms, then a split procedure header.
// expect: * accept
// source: deferred item 23 repro (docs/deferred-work.md), 2026-11-09
codeunit 50101 X
{
    Permissions = tabledata T1 = r,
#if CLEAN25
                  tabledata T2 = i;
#else
                  tabledata T3 = m;
#endif

#if CLEAN25
    procedure A()
#else
    procedure A(B: Integer)
#endif
    begin
    end;
}

table 50101 T1
{
    fields
    {
        field(1; F; Integer) { }
    }
}
table 50102 T2
{
    fields
    {
        field(1; F; Integer) { }
    }
}
table 50103 T3
{
    fields
    {
        field(1; F; Integer) { }
    }
}
table 50104 T4
{
    fields
    {
        field(1; F; Integer) { }
    }
}
