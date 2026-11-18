// expect: * accept
// runtime: 15.0 18.0
// source: gh issue #43: a namespace-qualified interface parent after `extends`, alone and with a second parent; and two plain parents
namespace My.Ns;
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface "IBar" extends My.Ns.IFoo
{
    procedure Extra1();
}
interface "IBar2" extends My.Ns.IFoo, IBaz
{
    procedure Extra2();
}
interface "IBar3" extends IFoo, IBaz
{
    procedure Extra3();
}
