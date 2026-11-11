// probe: F(1, I is Option, 2);
// source: state review C2 review: an interface named like a type keyword; main ERRORs or misparses, C2 parses it (CHANGELOG)
// expect: * accept
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
        J: Interface IFoo;
    begin
        F(1, I is Option, 2);
    end;
    procedure F(A: Integer; X: Boolean; C: Integer) begin end;
}
interface IFoo
{
    procedure X();
}
interface "Option" { procedure X(); }
