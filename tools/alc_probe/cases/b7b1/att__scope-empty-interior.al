// B7b-1 Task 2 route attribute-arguments (spec 4.2): empty interior of a one-argument attribute; X defined is the control.
// expect: * accept
// expect: !X reject(AL0238)
// source: predicted by B7b-1 Task 2 (spec 4.2), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    [Scope(
#if X
        'OnPrem'
#endif
    )]
    procedure Q()
    begin
    end;
}
