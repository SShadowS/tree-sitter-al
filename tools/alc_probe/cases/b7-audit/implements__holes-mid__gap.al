// B7a Task 10 witness (GAP): family implements, base placement holes-mid, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#holes-mid
// Fixture b7_gap_implements_test.txt#B7a GAP: implements / holes-mid (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:implements_clause:2.0.0@codeunit_declaration%23holes-mid#0
// expect: !X accept
// expect: X reject(AL0107)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:implements_clause:2.0.0@codeunit_declaration#holes-mid in tools/b7_audit/evidence.jsonl.gz
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
,
#endif
IBar

{
}
