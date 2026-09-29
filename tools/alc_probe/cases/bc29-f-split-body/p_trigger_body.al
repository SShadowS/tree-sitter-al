// expect: * accept
// source: docs/bc29-parse-gaps.md family F (ACCEPT in both configs), commit 9e7f9f0
codeunit 50100 T
{
    trigger OnRun()
#if not C28
    var
        I: Integer;
    begin
        if I = 0 then
            Error('x');
#else
    begin
#endif
        Message('y');
    end;
}
