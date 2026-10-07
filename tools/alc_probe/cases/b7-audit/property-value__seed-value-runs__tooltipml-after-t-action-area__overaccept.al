// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement seed:value-runs__tooltipml-after-t-action-area, 1 cells; representative seed:value-runs__tooltipml-after-t-action-area
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / seed:value-runs__tooltipml-after-t-action-area (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104) but the parser is clean; representative seed:value-runs__tooltipml-after-t-action-area#0
// expect: !X !Z accept
// expect: !X Z accept
// expect: X !Z reject(AL0104)
// expect: X Z reject(AL0104)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__tooltipml-after-t-action-area in tools/b7_audit/evidence.jsonl.gz
page 50100 P { PageType = RoleCenter; actions { area(Embedding) {
ToolTipML =
#if X
ENU='a'
#endif
#if not X
ENU='b';
#else
ENU='c';
#endif
#if Z
action(B) { RunObject = page P; }
#endif
action(A) { RunObject = page P; } } } }
