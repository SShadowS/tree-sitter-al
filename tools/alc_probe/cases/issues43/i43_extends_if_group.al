// expect: * accept
// source: gh issue #43 follow-up: an #if group between interface parents after `extends`
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IBar
    extends IFoo
#if X
    , IBaz
#endif
{
    procedure Extra();
}
