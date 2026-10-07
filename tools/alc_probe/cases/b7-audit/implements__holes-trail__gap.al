// B7a Task 10 witness (GAP): family implements, base placement holes-trail, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#holes-trail
// Fixture strict_conditional_implements_test.txt#strict implements MIXED: separator-only group after the last item (holes-trail)#0
// expect: !X accept
// expect: X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:implements_clause:2.0.0@codeunit_declaration#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
IFoo , IBar
#if X
,
#endif

{
}
