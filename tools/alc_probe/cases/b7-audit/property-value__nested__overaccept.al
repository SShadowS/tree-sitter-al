// B7b-2 Task 6 witness (REJECTED/over-accepts(syntax)): family property-value, base placement nested, 24 cells; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#nested/comparison
// Fixture b7_gap_property_value_test.txt#B7b-2 Task 6 REJECTED/over-accepts(syntax): property-value / nested (24 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0198) but the parser is clean; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin%23nested/comparison#0
// expect: !TPL !TPL2 !X !Y accept
// expect: !TPL !TPL2 !X Y accept
// expect: !TPL !TPL2 X !Y accept
// expect: !TPL !TPL2 X Y accept
// expect: !TPL TPL2 !X !Y accept
// expect: !TPL TPL2 !X Y accept
// expect: !TPL TPL2 X !Y accept
// expect: !TPL TPL2 X Y accept
// expect: TPL !TPL2 !X !Y accept
// expect: TPL !TPL2 !X Y accept
// expect: TPL !TPL2 X !Y accept
// expect: TPL !TPL2 X Y accept
// expect: TPL TPL2 !X !Y accept
// expect: TPL TPL2 !X Y accept
// expect: TPL TPL2 X !Y reject(AL0104,AL0198)
// expect: TPL TPL2 X Y reject(AL0104,AL0198)
// source: recorded by B7b-2 Task 6, 2026-10-20: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#nested/comparison in tools/b7_audit/evidence.jsonl.gz
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
controladdin CA2
{
#if TPL2
                VerticalStretch =
#if TPL
                    
true
#if X
= true
#if Y
= false
#endif
#endif
;
#else
                    true;
#endif
#endif
}
