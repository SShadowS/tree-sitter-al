// expect: * accept
// source: item 102 re-review of 75ac1db3 (scratchpad rv102b/probes/nv_nested_empty_then_var_in_arm.al)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
#if B
#endif
    var
        V: Integer;
#endif
    begin
    end;

    procedure P()
#if A
#if B
#endif
    var
        V: Integer;
#endif
    begin
    end;

    procedure Q(): Integer
#if A
#if B
#endif
    var
        V: Integer;
#endif
    begin
        exit(1);
    end;
}
