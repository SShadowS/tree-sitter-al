// B7a Task 10 witness (GAP): family implements, base placement trail, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#trail
// Fixture strict_conditional_implements_test.txt#strict implements MIXED: trailing group after the separator (trail)#0
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
