// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family where-filter, base placement holes-mid, 15 cells; representative occ:_where_branch:0.0@preproc_conditional_where#holes-mid
// Fixture b7_gap_where_filter_test.txt#B7a REJECTED/over-accepts(syntax): where-filter / holes-mid (15 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0292) but the parser is clean; representative occ:_where_branch:0.0@preproc_conditional_where%23holes-mid#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0104,AL0107,AL0292)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_branch:0.0@preproc_conditional_where#holes-mid in tools/b7_audit/evidence.jsonl.gz
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
N = const(1) ,
#if X
,
#endif
"B" = const(true)

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
