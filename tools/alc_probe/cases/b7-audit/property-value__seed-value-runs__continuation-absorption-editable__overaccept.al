// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement seed:value-runs__continuation-absorption-editable, 1 cells; representative seed:value-runs__continuation-absorption-editable
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / seed:value-runs__continuation-absorption-editable (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0219) but the parser is clean; representative seed:value-runs__continuation-absorption-editable#0
// expect: !X !Y reject(AL0104,AL0219)
// expect: !X Y reject(AL0219)
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__continuation-absorption-editable in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(4; Flag; Boolean) { } } }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Caption =
#if X
    'a';
#endif
#if Y
    Editable = false;
#endif
} } } }
