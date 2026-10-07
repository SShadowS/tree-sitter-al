// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement seed:value-runs__generic-three-group-run-inside, 1 cells; representative seed:value-runs__generic-three-group-run-inside
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / seed:value-runs__generic-three-group-run-inside (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0198,AL0219) but the parser is clean; representative seed:value-runs__generic-three-group-run-inside#0
// expect: !X !Y !Z reject(AL0104,AL0219)
// expect: !X !Y Z accept
// expect: !X Y !Z accept
// expect: !X Y Z reject(AL0104,AL0198)
// expect: X !Y !Z accept
// expect: X !Y Z reject(AL0104,AL0198)
// expect: X Y !Z reject(AL0104,AL0198)
// expect: X Y Z reject(AL0104,AL0198)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__generic-three-group-run-inside in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Caption =
#if X
    'a';
#endif
#if Y
    'b';
#endif
#if Z
    'c';
#endif
} } } }
