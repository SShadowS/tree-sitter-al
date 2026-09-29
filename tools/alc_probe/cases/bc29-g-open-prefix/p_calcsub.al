// expect: * accept
// source: docs/bc29-parse-gaps.md family G (ACCEPT in both configs), commit 07758c6
codeunit 50100 T
{
    procedure P(Blocked: Boolean)
    var
        A, B: Integer;
    begin
#if not C28
        B := 0;
        if Blocked then
            Message('y')
        else begin
#endif
            A := 1;
#if not C28
        end;
#endif
    end;
}
