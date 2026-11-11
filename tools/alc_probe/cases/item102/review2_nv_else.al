// expect: * accept
// source: item 102 re-review of 75ac1db3 (scratchpad rv102b/probes/nv_else.al)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
    var
        V: Integer;
#else
#if B
#endif
    var
        W: Integer;
#endif
    begin
    end;

    procedure P()
#if A
    var
        V: Integer;
#else
#if B
#endif
    var
        W: Integer;
#endif
    begin
    end;

    procedure Q(): Integer
#if A
    var
        V: Integer;
#else
#if B
#endif
    var
        W: Integer;
#endif
    begin
        exit(1);
    end;
}
