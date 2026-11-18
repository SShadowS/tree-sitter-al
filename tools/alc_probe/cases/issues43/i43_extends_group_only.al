// expect: X accept
// expect: !X accept
// source: gh issue #43 review: a group as the only parent, no #else (X=0 leaves an empty extends)
interface IFoo
{
    procedure Exec();
}
interface IBar extends
#if X
    IFoo
#endif
{
    procedure Extra();
}
