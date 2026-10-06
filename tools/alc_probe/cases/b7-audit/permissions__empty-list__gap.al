// B7a Task 10 witness (GAP): family permissions, base placement empty-list, 3 cells; representative occ:_permission_run:0.1.0.0@permissions_property#empty-list
// Fixture b7_gap_permissions_test.txt#B7a GAP: permissions / empty-list (3 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_permission_run:0.1.0.0@permissions_property%23empty-list#0
// expect: !TPL !X reject(AL0104)
// expect: !TPL X accept
// expect: TPL !X reject(AL0104)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_permission_run:0.1.0.0@permissions_property#empty-list in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
table 50109 T2
{
    fields
    {
        field(1; K; Code[20]) { }
    }
}
table 50114 T3
{
    fields
    {
        field(1; K; Code[20]) { }
    }
}
codeunit 50101 P
{
    Permissions =
#if TPL
#endif
        
#if X
tabledata T = R , tabledata T2 = R
#endif
,
#if TPL
        tabledata T3 = R;
#else
        tabledata T3 = RM;
#endif
}
