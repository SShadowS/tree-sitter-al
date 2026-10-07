// B7a Task 10 witness (GAP): family where-filter, base placement first-replace, 15 cells; representative occ:_where_branch:0.0@preproc_conditional_where#first-replace
// Fixture b7_gap_where_filter_test.txt#B7a GAP: where-filter / first-replace (15 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_where_branch:0.0@preproc_conditional_where%23first-replace#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_branch:0.0@preproc_conditional_where#first-replace in tools/b7_audit/evidence.jsonl.gz
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
#if X
N = const(1)
#else
"B" = const(true)
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
