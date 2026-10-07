// B7b-1 Task 13 witness (REJECTED/over-accepts(syntax)): family implements, base placement empty-list, 9 cells; representative occ:implements_clause:2.0.0@codeunit_declaration#empty-list (the B7a GAP witness of this shape, renamed: the strict list parses every configuration, alc still rejects one)
// Fixture strict_conditional_implements_test.txt#strict implements MIXED: the whole list in one group, no %23else (empty-list)#0
// expect: !X reject(AL0107)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:implements_clause:2.0.0@codeunit_declaration#empty-list in tools/b7_audit/evidence.jsonl.gz
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
#endif

{
}
