// probe: namespace-qualified name
// source: state review C2 review: a namespace-qualified name after is; ERROR on main and C2 (deferred item 101)
// expect: * accept
namespace My.NS;
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
    begin
        B := I is My.NS.IFoo;
    end;
}
interface IFoo
{
    procedure X();
}
