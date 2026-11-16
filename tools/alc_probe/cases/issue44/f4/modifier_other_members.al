// The same group in a table, a page, a report and a pageextension.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }

#if A
    internal
#endif
    procedure P1()
    begin
    end;
}
page 50100 P
{
#if A
    local
#endif
    procedure P1()
    begin
    end;
}
report 50100 R
{
#if A
    local
#endif
    procedure P1()
    begin
    end;
}
pageextension 50101 PE extends P
{
#if A
    internal
#endif
    procedure P2()
    begin
    end;
}
