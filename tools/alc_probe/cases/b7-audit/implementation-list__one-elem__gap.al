// B7a Task 10 witness (GAP): family implementation-list, base placement one-elem, 12 cells; representative occ:_impl_value_branch:0.0@implementation_value_list#one-elem
// Fixture b7_gap_implementation_list_test.txt#B7a GAP: implementation-list / one-elem (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_impl_value_branch:0.0@implementation_value_list%23one-elem#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_impl_value_branch:0.0@implementation_value_list#one-elem in tools/b7_audit/evidence.jsonl.gz
interface IFoo
{
}

interface IBar
{
}

interface IBaz
{
}

codeunit 50103 Impl implements IFoo, IBar, IBaz
{
}

enum 50108 En implements IFoo, IBar, IBaz
{
    DefaultImplementation = IFoo = Impl, IBar = Impl, IBaz = Impl;
    value(0; V0)
    {
    Implementation =
#if TPL
        IFoo = Impl,
#else
        
#if X
IFoo = Impl , IBar = Impl
#else
IFoo = Impl
#endif
,

#endif
        IBaz = Impl;
    }
}
