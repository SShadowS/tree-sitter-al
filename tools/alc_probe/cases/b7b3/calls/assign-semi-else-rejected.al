// B7b-3 Task 4 fix round 1: orphan `else` after a terminated assignment (deferred item 43)
// expect: * reject(AL0110)
// source: B7b-3 Task 4 fix round 1, 2026-10-08
codeunit 50100 P
{
    procedure M(C: Boolean)
    var
        X: Integer;
    begin
        if C then X := 1; else X := 2;
    end;
}
