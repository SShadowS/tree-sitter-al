// expect: * accept
// source: gh issue #43 follow-up: a group holding a namespace-qualified parent
namespace My.Ns;
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IBar
    extends IBaz
#if X
    , My.Ns.IFoo
#endif
{
    procedure Extra();
}
