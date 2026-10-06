// B7a Task 10 witness (GAP): family expression-tail, base placement seed:expression-statement__b7-gap-assign-semicolon-in-arms, 1 cells; representative seed:expression-statement__b7-gap-assign-semicolon-in-arms
// Fixture b7_gap_expression_tail_test.txt#B7a GAP: expression-tail / seed:expression-statement__b7-gap-assign-semicolon-in-arms (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:expression-statement__b7-gap-assign-semicolon-in-arms#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:expression-statement__b7-gap-assign-semicolon-in-arms in tools/b7_audit/evidence.jsonl.gz
codeunit 50101 Probe
{
    procedure Foo() begin end;
    procedure Main()
    var A: Integer; B: Integer; X: Integer;
    begin
        B := A
#if X
            + 1;
        Foo();
#else
        ;
#endif
    end;
}
