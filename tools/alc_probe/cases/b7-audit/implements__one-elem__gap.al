// B7a Task 10 witness (GAP): family implements, base placement one-elem, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#one-elem
// Fixture strict_conditional_implements_test.txt#strict implements: the whole list in the arms of one group (one-elem)#0
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
