// expect: * accept
// source: docs/bc29-parse-gaps.md family G (ACCEPT in both configs), commit 07758c6
codeunit 50100 T
{
    procedure P(No: Integer)
    var
        A, B, C, D: Integer;
    begin
        if No < 1 then
            A := 1
#if not C27
        else begin
#else
        else
#endif
            B := 2;
#if not C27
            C := 3;
        end;
#endif
        D := 4;
    end;
}
