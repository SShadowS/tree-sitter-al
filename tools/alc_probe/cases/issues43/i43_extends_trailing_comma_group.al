// expect: * reject(AL0301)
// source: gh issue #43 review: alc rejects a trailing comma before an empty/absent group; the parser accepts it (deferred item 44 inventory)
interface IFoo
{
    procedure Exec();
}
interface IBar extends IFoo ,
#if X
#endif
{
}
