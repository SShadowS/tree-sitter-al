// expect: * accept
// source: gh issue #43 follow-up: an #if/#else choosing the second parent
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IQux
{
    procedure Q();
}
interface IBar
    extends IFoo
#if X
    , IBaz
#else
    , IQux
#endif
{
    procedure Extra();
}
