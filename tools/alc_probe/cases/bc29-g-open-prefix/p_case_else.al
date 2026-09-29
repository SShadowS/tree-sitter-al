// expect: * accept
// source: docs/bc29-parse-gaps.md family G (ACCEPT in both configs), commit 07758c6
codeunit 50100 T
{
    procedure P(X: Integer)
    var
        A, B, C: Integer;
    begin
        case X of
            1:
                A := 1
#if C29
            else
#else
            else begin
                B := 2;
#endif
                C := 3;
#if not C29
            end;
#endif
        end;
    end;
}
