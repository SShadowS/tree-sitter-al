// expect: * accept
// runtime: 15.0 18.0
// source: gh issue #43 review: alc accepts an EMPTY extends list (contrast `codeunit C implements { }`, AL0107), also when implemented
interface IFoo
{
    procedure Exec();
}
interface IBar extends
{
    procedure Extra();
}
codeunit 50100 C implements IBar
{
    procedure Extra()
    begin
    end;
}
