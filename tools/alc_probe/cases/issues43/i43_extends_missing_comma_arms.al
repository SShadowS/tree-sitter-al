// expect: * reject(AL0104,AL0198)
// source: gh issue #43 review: alc rejects a parent after a parent with no comma (the group arms supply none); the parser accepts it (deferred item 44 inventory)
interface IFoo
{
    procedure Exec();
}
interface IBaz
{
    procedure Go();
}
interface IBar extends IFoo
#if X
    IBaz
#else
    IBaz
#endif
{
}
