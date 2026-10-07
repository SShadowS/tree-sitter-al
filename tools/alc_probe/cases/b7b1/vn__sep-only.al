// B7b-1 Task 2 var-name attribute probe (spec 5.1): separator-only group (X undefined leaves two names with no comma)
// Fixture strict_conditional_var_names_attr_test.txt#strict var names attr: separator-only group, MIXED (sep-only)#0
// expect: * accept
// expect: !X reject(AL0104,AL0107)
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        A
#if X
        ,
#endif
        B: Integer;

    procedure Q()
    begin
    end;
}
