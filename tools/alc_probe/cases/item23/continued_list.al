// Deferred item 23: one arm ends the Permissions list with `;`, the other continues it into a second #if group.
// expect: * accept
// source: deferred item 23, 2026-11-09 (why a group after a `;`-arm group must still be able to extend the list)
codeunit 50101 X
{
    Permissions = tabledata T1 = r,
#if CLEAN25
                  tabledata T2 = i;
#else
                  tabledata T3 = m,
#endif
#if not CLEAN25
                  tabledata T4 = d;
#endif

    procedure A()
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
