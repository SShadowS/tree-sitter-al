// B7a Task 10 witness (GAP): family unassigned, base placement seed:expression-statement__torn-exit-plus, 1 cells; representative seed:expression-statement__torn-exit-plus
// Fixture b7_gap_unassigned_test.txt#B7a GAP: unassigned / seed:expression-statement__torn-exit-plus (1 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative seed:expression-statement__torn-exit-plus#0
// expect: !A accept
// expect: A reject(AL0104,AL0111)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:expression-statement__torn-exit-plus in tools/b7_audit/evidence.jsonl.gz
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main(): Integer
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        exit(1)
#if A
        + 2
#endif
        ;
    end;
}
