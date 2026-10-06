// B7a Task 10 witness (GAP): family table-relation, base placement elif, 30 cells; representative occ:_table_relation_arm_t:0.3@declaration_body#elif
// Fixture b7_gap_table_relation_test.txt#B7a GAP: table-relation / elif (30 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_table_relation_arm_t:0.3@declaration_body%23elif#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_table_relation_arm_t:0.3@declaration_body#elif in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; RK; Code[20])
        {
            TableRelation =
#if TPL
                
T
#if X
;
#elif Y
;
#else
;
#endif

#else
                T.K;
#endif
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
