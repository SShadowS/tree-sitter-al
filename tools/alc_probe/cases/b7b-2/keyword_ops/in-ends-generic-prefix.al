// B7b-2 Task 4 fix round 1: a generic operand prefix (inside `and`) whose arms end in `in` (spec 5.3 scope, amendment Task 4 item 6)
// expect: * accept
// source: B7b-2 Task 4 fix round 1, 2026-10-20
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; J: Integer; B: Boolean; Ok: Boolean;
    begin
        B := Ok and
#if X
        I in
#else
        J in
#endif
        [1];
    end;
}
