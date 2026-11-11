// expect: * accept
// source: item 102 re-review of 75ac1db3 (scratchpad rv102b/probes/nv_pragma_nested.al)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
#if B
#pragma warning disable AA0001
#endif
    var
        V: Integer;
#endif
#if C
#endif
    begin
    end;

    procedure P()
#if A
#if B
#pragma warning disable AA0001
#endif
    var
        V: Integer;
#endif
#if C
#endif
    begin
    end;

    procedure Q(): Integer
#if A
#if B
#pragma warning disable AA0001
#endif
    var
        V: Integer;
#endif
#if C
#endif
    begin
        exit(1);
    end;
}
