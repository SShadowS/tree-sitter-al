// B7b-2 Task 4 fix round 1: `in` in the B3 operator-only form, every arm one `in` (spec 5.3 scope, amendment Task 4 item 6)
// expect: * accept
// source: B7b-2 Task 4 fix round 1, 2026-10-20
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; J: Integer; B: Boolean; Ok: Boolean;
    begin
        B := Ok
#if X
        in
#else
        in
#endif
        [true];
    end;
}
