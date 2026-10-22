// B7b-2 Task 4 fix round 1: a typed `in` prefix arm with a continuation before its keyword (spec 5.3 scope, amendment Task 4 item 6)
// expect: * accept
// source: B7b-2 Task 4 fix round 1, 2026-10-20
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; J: Integer; B: Boolean; Ok: Boolean;
    begin
        B := Ok in
#if X
        [true] and Ok in
#endif
        [false];
    end;
}
