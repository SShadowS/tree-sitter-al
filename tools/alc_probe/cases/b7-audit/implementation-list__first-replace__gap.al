// B7a Task 10 witness (GAP): family implementation-list, base placement first-replace, 3 cells; representative occ:_impl_value_run:0.1.0.0@implementation_value_list#first-replace
// Fixture b7_gap_implementation_list_test.txt#B7a GAP: implementation-list / first-replace (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_impl_value_run:0.1.0.0@implementation_value_list%23first-replace#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_impl_value_run:0.1.0.0@implementation_value_list#first-replace in tools/b7_audit/evidence.jsonl.gz
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
#if X
IFoo = Impl
#else
IBar = Impl
#endif
, IBaz = Impl
;
    }
}
