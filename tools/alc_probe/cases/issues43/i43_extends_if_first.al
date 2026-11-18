// expect: * accept
// source: gh issue #43 follow-up: a group as the first parent (group alone with #else, and group then a plain parent)
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IBar
    extends
#if X
    IFoo
#else
    IBaz
#endif
{
    procedure Extra();
}
interface IBar2
    extends
#if X
    IFoo,
#endif
    IBaz
{
    procedure Extra2();
}
