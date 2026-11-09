// Deferred item 23: a list opened by an empty #if, its `;` in the arms of a later group, then a #if var section.
// expect: * accept
// source: deferred item 23, 2026-11-09 (the _permission_list_empty_open host of permissions_property)
codeunit 50101 P
{
    Permissions =
#if X
#endif
                  tabledata T1 = r,
#if Y
                  tabledata T2 = i;
#else
                  tabledata T3 = m;
#endif
#if X
    var
        G: Integer;
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
