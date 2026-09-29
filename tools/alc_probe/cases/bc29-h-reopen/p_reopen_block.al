// expect: * accept
// source: docs/bc29-parse-gaps.md family H (ACCEPT x2), commit d2ddeac
codeunit 50100 T
{
    procedure P(A: Boolean; D: Boolean)
    var
        X, Y: Integer;
    begin
        if A then begin
            X := 1;
#if not C
        end else
            if D then begin
                Y := 1;
#endif
            end;
    end;
}
