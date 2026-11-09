// Deferred item 23: a Permissions list whose `;` is inside the #if arms, then a #if group holding a whole procedure.
// expect: * accept
// source: deferred item 23, 2026-11-09 (the follower need not be a split: any group that opens no permission)
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
    begin
    end;
#endif
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
