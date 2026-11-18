// expect: !X reject(AL0301)
// expect: X reject(AL0107)
// source: gh issue #43 review: alc rejects a trailing comma then a group that starts with a comma; the parser accepts it (deferred item 44 inventory)
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IBar extends IFoo ,
#if X
    , IBaz
#endif
{
}
