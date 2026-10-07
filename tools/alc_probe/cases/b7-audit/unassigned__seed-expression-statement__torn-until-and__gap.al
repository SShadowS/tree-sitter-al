// B7a Task 10 witness (GAP): family unassigned, base placement seed:expression-statement__torn-until-and, 1 cells; representative seed:expression-statement__torn-until-and
// Fixture b7_gap_unassigned_test.txt#B7a GAP: unassigned / seed:expression-statement__torn-until-and (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:expression-statement__torn-until-and#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:expression-statement__torn-until-and in tools/b7_audit/evidence.jsonl.gz
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main()
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        repeat
            Foo();
        until C
#if X
            and (C)
#endif
        ;
    end;
}
