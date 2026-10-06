// B7a Task 10 witness (GAP): family implements, base placement one-elem, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#one-elem
// Fixture b7_gap_implements_test.txt#B7a GAP: implements / one-elem (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:implements_clause:2.0.0@codeunit_declaration%23one-elem#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:implements_clause:2.0.0@codeunit_declaration#one-elem in tools/b7_audit/evidence.jsonl.gz
interface IFoo
{
}

interface IBar
{
}

interface IBaz
{
}

codeunit 50111 C2 implements 
#if X
IFoo , IBar
#else
IFoo
#endif

{
}
