// B7b-3 Task 4 fix round 1: orphan `else` after a terminated call (deferred item 43)
// expect: * reject(AL0110)
// source: B7b-3 Task 4 fix round 1, 2026-10-08
codeunit 50100 P
{
    procedure M(C: Boolean)
    begin
        if C then Bar; else Bar;
    end;

    procedure Bar()
    begin
    end;
}
