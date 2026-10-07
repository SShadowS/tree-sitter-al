// B7a Task 10 witness (GAP): family option-members, base placement holes-mid, 24 cells; representative occ:_option_members_branch_c:0.0@option_member_list#holes-mid
// Fixture b7_gap_option_members_test.txt#B7a GAP: option-members / holes-mid (24 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_option_members_branch_c:0.0@option_member_list%23holes-mid#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_option_members_branch_c:0.0@option_member_list#holes-mid in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; O2; Option)
        {
            OptionMembers =
#if TPL
            
,
A ,
#if X
,
#endif
B
,

#endif
#if not TPL
            A,B,
#endif
            C;
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
