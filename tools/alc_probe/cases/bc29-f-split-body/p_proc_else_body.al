// expect: * accept
// source: docs/bc29-parse-gaps.md family F (ACCEPT in both configs), commit 9e7f9f0
codeunit 50100 T
{
    procedure P(): Text
#if C29
    var
        I: Integer;
    begin
        if I = 0 then
            exit('a');
#else
    begin
        exit('b');
#endif
    end;
}
