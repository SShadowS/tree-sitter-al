// expect: * accept
// source: review #43: split header with extends
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
#if X
interface IBar extends IFoo, IBaz
#else
interface IBar extends IFoo
#endif
{
    procedure Extra();
}
