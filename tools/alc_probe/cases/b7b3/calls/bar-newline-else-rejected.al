// B7b-3 Task 4 fix round 1: orphan `else` on the line after a bare call, no if (deferred item 43)
// expect: * reject(AL0104,AL0110,AL0111,AL0224)
// source: B7b-3 Task 4 fix round 1, 2026-10-08
codeunit 50100 P
{
    procedure M()
    begin
        Bar
        else
    end;

    procedure Bar()
    begin
    end;
}
