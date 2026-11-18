// expect: * accept
// source: gh issue #43 follow-up: an #if/#elif/#else chain between parents
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
#elif Y
    , IQux
#else
    , IBaz
#endif
{
    procedure Extra();
}
