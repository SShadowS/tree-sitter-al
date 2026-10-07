// B7a Task 10 witness (GAP): family where-filter, base placement holes-trail, 9 cells; representative occ:_where_run:0.1.0.0@preproc_conditional_where#holes-trail
// Fixture b7_gap_where_filter_test.txt#B7a GAP: where-filter / holes-trail (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_where_run:0.1.0.0@preproc_conditional_where%23holes-trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0104,AL0107,AL0292)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_run:0.1.0.0@preproc_conditional_where#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
                
N = const(1) , O = const(A)
#if X
,
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
