// B7a Task 10 witness (GAP): family permissions, base placement seed:task4-permission-arm-bare-semicolon, 1 cells; representative seed:task4-permission-arm-bare-semicolon
// Fixture b7_gap_permissions_test.txt#B7a GAP: permissions / seed:task4-permission-arm-bare-semicolon (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:task4-permission-arm-bare-semicolon#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:task4-permission-arm-bare-semicolon in tools/b7_audit/evidence.jsonl.gz
table 50100 T { fields { field(1; K; Integer) { } } }
table 50101 T2 { fields { field(1; K; Integer) { } } }
permissionset 50102 PS
{
    Assignable = true;
    Permissions = tabledata T = R
#if X
        , tabledata T2 = R;
#else
        ;
#endif
}
