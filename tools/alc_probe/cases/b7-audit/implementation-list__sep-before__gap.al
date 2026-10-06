// B7a Task 10 witness (GAP): family implementation-list, base placement sep-before, 3 cells; representative occ:_impl_value_run:0.1.0.0@implementation_value_list#sep-before
// Fixture b7_gap_implementation_list_test.txt#B7a GAP: implementation-list / sep-before (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_impl_value_run:0.1.0.0@implementation_value_list%23sep-before#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_impl_value_run:0.1.0.0@implementation_value_list#sep-before in tools/b7_audit/evidence.jsonl.gz
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
IFoo = Impl
#if X
, IBar = Impl
#endif
, IBaz = Impl
;
    }
}
