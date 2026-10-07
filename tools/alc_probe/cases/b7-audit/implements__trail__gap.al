// B7a Task 10 witness (GAP): family implements, base placement trail, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#trail
// Fixture b7_gap_implements_test.txt#B7a GAP: implements / trail (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:implements_clause:2.0.0@codeunit_declaration%23trail#0
// expect: !X reject(AL0301)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:implements_clause:2.0.0@codeunit_declaration#trail in tools/b7_audit/evidence.jsonl.gz
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
IFoo ,
#if X
IBar
#endif

{
}
