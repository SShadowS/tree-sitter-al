// expect: * accept
// source: docs/bc29-parse-gaps.md family G (ACCEPT in both configs), commit 07758c6
codeunit 50100 T
{
    procedure P(IsHandled: Boolean; Y: Boolean)
    var
        B, C: Integer;
    begin
        if not IsHandled then
#if not C28
        begin
            if Y then begin
                B := 1;
            end else
#endif
                C := 2;
#if not C28
        end;
#endif
    end;
}
