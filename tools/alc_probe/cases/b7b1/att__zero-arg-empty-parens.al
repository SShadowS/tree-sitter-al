// B7b-1 Task 2 route attribute-arguments (spec 4.2 case 2): empty parentheses on a zero-argument attribute;
// the bare form is the control.
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 4.2), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
#if X
    [NonDebuggable()]
#else
    [NonDebuggable]
#endif
    procedure Q()
    begin
    end;
}
