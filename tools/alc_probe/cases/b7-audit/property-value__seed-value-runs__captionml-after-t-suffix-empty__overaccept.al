// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement seed:value-runs__captionml-after-t-suffix-empty, 1 cells; representative seed:value-runs__captionml-after-t-suffix-empty
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / seed:value-runs__captionml-after-t-suffix-empty (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104) but the parser is clean; representative seed:value-runs__captionml-after-t-suffix-empty#0
// expect: !X !Z accept
// expect: !X Z accept
// expect: X !Z reject(AL0104)
// expect: X Z reject(AL0104)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__captionml-after-t-suffix-empty in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; A; Code[20]) { } field(2; B; Code[20]) { } } }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.A) {
CaptionML =
#if X
ENU='a'
#endif
#if not X
ENU='b';
#else
ENU='c';
#endif
#if Z
#endif
;
} } } }
