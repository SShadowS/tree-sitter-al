// B7a Task 10 witness (GAP): family permissions, base placement adjacent-indep, 21 cells; representative occ:_permission_branch:0.0@tabledata_permission_list#adjacent-indep
// Fixture b7_gap_permissions_test.txt#B7a GAP: permissions / adjacent-indep (21 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_permission_branch:0.0@tabledata_permission_list%23adjacent-indep#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y reject(AL0393)
// expect: !TPL X !Y accept
// expect: !TPL X Y reject(AL0393)
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_permission_branch:0.0@tabledata_permission_list#adjacent-indep in tools/b7_audit/evidence.jsonl.gz
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
        tabledata T = R,
#else
        
tabledata T2 = R
#if X
, tabledata T = R
#endif
#if Y
, tabledata T3 = R
#endif
,

#endif
        tabledata T3 = R;
}
