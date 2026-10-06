// B7a Task 10 witness (GAP): family table-relation, base placement empty, 3 cells; representative occ:_table_relation_branch:1.0@preproc_conditional_table_relation#empty
// Fixture b7_gap_table_relation_test.txt#B7a GAP: table-relation / empty (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_table_relation_branch:1.0@preproc_conditional_table_relation%23empty#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_table_relation_branch:1.0@preproc_conditional_table_relation#empty in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; RK; Code[20])
        {
            TableRelation = if (B = const(true)) T else
#if TPL
                
T.K
#if X
#endif
;

#else
                T;
#endif
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
