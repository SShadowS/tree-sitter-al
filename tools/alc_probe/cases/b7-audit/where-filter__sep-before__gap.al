// B7a Task 10 witness (GAP): family where-filter, base placement sep-before, 15 cells; representative occ:_where_branch:0.0@preproc_conditional_where#sep-before
// Fixture b7_gap_where_filter_test.txt#B7a GAP: where-filter / sep-before (15 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_where_branch:0.0@preproc_conditional_where%23sep-before#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_branch:0.0@preproc_conditional_where#sep-before in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; C; Integer)
        {
            FieldClass = FlowField;
            CalcFormula = count(T where(K = field(K)
#if TPL
                
,
N = const(1)
#if X
, "B" = const(true)
#endif
, K = field(K)

#endif
                ));
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
