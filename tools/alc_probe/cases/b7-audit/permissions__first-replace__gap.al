// B7a Task 10 witness (GAP): family permissions, base placement first-replace, 18 cells; representative occ:_permission_branch:0.0@preproc_conditional_permissions#first-replace
// Fixture b7_gap_permissions_test.txt#B7a GAP: permissions / first-replace (18 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_permission_branch:0.0@preproc_conditional_permissions%23first-replace#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0393)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_permission_branch:0.0@preproc_conditional_permissions#first-replace in tools/b7_audit/evidence.jsonl.gz
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
    Permissions = tabledata T = R
#if TPL
        
,
#if X
tabledata T2 = R
#else
tabledata T = R
#endif
, tabledata T3 = R

#endif
        ;
}
