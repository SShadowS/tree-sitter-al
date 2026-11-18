// expect: * reject(AL0301)
// source: gh issue #43 review: alc rejects both arms being a bare comma; the parser accepts it (deferred item 44 inventory)
interface IFoo
{
    procedure Exec();
}
interface IBar extends IFoo
#if X
    ,
#else
    ,
#endif
{
}
