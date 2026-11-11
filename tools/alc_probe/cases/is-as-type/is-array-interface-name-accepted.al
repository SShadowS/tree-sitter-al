// probe: B := I is Array;
// source: state review C2 review: an interface named like a type keyword; main ERRORs or misparses, C2 parses it (CHANGELOG)
// expect: * accept
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
        J: Interface IFoo;
    begin
        B := I is Array;
    end;
}
interface IFoo
{
    procedure X();
}
interface "Array" { procedure X(); }
