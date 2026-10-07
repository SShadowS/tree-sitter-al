// B7a Task 10 witness (GAP): family where-filter, base placement adjacent-indep, 9 cells; representative occ:_where_run:0.1.0.0@preproc_conditional_where#adjacent-indep
// Fixture b7_gap_where_filter_test.txt#B7a GAP: where-filter / adjacent-indep (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_where_run:0.1.0.0@preproc_conditional_where%23adjacent-indep#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_run:0.1.0.0@preproc_conditional_where#adjacent-indep in tools/b7_audit/evidence.jsonl.gz
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
            CalcFormula = count(T where(K = field(K),
#if TPL
                
N = const(1)
#if X
, O = const(A)
#endif
#if Y
, "B" = const(true)
#endif
,

#endif
                B = const(true)));
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
