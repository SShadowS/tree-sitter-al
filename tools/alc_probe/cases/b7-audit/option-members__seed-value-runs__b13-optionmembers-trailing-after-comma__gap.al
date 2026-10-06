// B7a Task 10 witness (GAP): family option-members, base placement seed:value-runs__b13-optionmembers-trailing-after-comma, 1 cells; representative seed:value-runs__b13-optionmembers-trailing-after-comma
// Fixture b7_gap_option_members_test.txt#B7a GAP: option-members / seed:value-runs__b13-optionmembers-trailing-after-comma (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:value-runs__b13-optionmembers-trailing-after-comma#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__b13-optionmembers-trailing-after-comma in tools/b7_audit/evidence.jsonl.gz
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
    A
#endif
    , B;
} } }
