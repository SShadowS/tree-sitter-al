// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family permissions, base placement holes-lead, 33 cells; representative occ:_permission_branch:0.0@preproc_conditional_permissions#holes-lead
// Fixture b7_gap_permissions_test.txt#B7a REJECTED/over-accepts(syntax): permissions / holes-lead (33 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0393) but the parser is clean; representative occ:_permission_branch:0.0@preproc_conditional_permissions%23holes-lead#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0393)
// expect: TPL X reject(AL0104)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_permission_branch:0.0@preproc_conditional_permissions#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
,
#endif
tabledata T2 = R , tabledata T = R

#endif
        ;
}
