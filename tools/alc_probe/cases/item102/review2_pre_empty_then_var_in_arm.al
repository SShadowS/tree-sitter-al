// expect: * accept
// source: item 102 re-review of 75ac1db3 (scratchpad rv102b/probes/pre_empty_then_var_in_arm.al)
codeunit 50100 Demo
{
#if A
    procedure P()
#if B
#endif
    var
        V: Integer;
#else
    procedure P(I: Integer)
#endif
    begin
    end;
}
