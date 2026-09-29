// expect: * accept
// source: docs/bc29-parse-gaps.md family G (ACCEPT in both configs), commit 07758c6
codeunit 50100 T
{
    procedure P(X: Integer; A: Integer)
    var
        B, C: Integer;
    begin
        case X of
            1:
#if not C29
                if A = 0 then begin
                    B := 1;
                end else
#else
                if A <> 0 then
#endif
                    C := 2;
            2:
                C := 3;
        end;
    end;
}
