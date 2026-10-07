// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family implementation-list, base placement holes-mid, 15 cells; representative occ:_impl_value_branch:0.0@implementation_value_list#holes-mid
// Fixture b7_gap_implementation_list_test.txt#B7a REJECTED/over-accepts(syntax): implementation-list / holes-mid (15 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0107) but the parser is clean; representative occ:_impl_value_branch:0.0@implementation_value_list%23holes-mid#0
// expect: !TPL !X accept
// expect: !TPL X reject(AL0107)
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_impl_value_branch:0.0@implementation_value_list#holes-mid in tools/b7_audit/evidence.jsonl.gz
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
        
IFoo = Impl ,
#if X
,
#endif
IBar = Impl
,

#endif
        IBaz = Impl;
    }
}
