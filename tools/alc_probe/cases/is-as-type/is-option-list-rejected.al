// State review 2026-11 (candidate C2): alc reads a NAME after `is`; an Option member list is a syntax error.
// source: docs/state-review-2026-11.md section B, C2
// expect: * reject(AL0104,AL0111)
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
    begin
        B := I is Option A,B;
    end;
}
interface IFoo
{
    procedure X();
}
