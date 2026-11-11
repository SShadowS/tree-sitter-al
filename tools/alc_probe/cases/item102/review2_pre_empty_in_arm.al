// expect: * accept
// source: item 102 re-review of 75ac1db3 (scratchpad rv102b/probes/pre_empty_in_arm.al)
codeunit 50100 Demo
{
#if A
    procedure P()
#if B
#endif
#else
    procedure P(I: Integer)
#endif
    begin
    end;

#if A
    trigger OnRun()
#if B
#endif
#else
    trigger OnRun()
#endif
    begin
    end;
}
