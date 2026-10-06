// B7a Task 10 witness (GAP): family implementation-list, base placement seed:task4-implementation-arm-comma-after-endif, 1 cells; representative seed:task4-implementation-arm-comma-after-endif
// Fixture b7_gap_implementation_list_test.txt#B7a GAP: implementation-list / seed:task4-implementation-arm-comma-after-endif (1 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative seed:task4-implementation-arm-comma-after-endif#0
// expect: !X reject(AL0596)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:task4-implementation-arm-comma-after-endif in tools/b7_audit/evidence.jsonl.gz
interface IFoo { procedure Bar(); }
interface IBar { procedure Bar(); }
interface IBaz { procedure Bar(); }
codeunit 50101 Impl implements IFoo, IBar, IBaz { procedure Bar() begin end; }
table 50100 T { fields { field(1; K; Integer) { } } }
enum 50102 E implements IFoo, IBar, IBaz
{
    value(0; V0)
    {
        Implementation = IFoo = Impl
#if X
            , IBar = Impl
#endif
            , IBaz = Impl;
    }
}
