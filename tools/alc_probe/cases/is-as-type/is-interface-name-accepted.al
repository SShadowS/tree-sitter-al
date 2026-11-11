// State review 2026-11 (candidate C2): the control. A name after `is` / `as` is accepted.
// source: docs/state-review-2026-11.md section B, C2
// expect: * accept
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
        J: Interface IFoo;
    begin
        B := I is IFoo;
        J := I as IFoo;
    end;
}
interface IFoo
{
    procedure X();
}
