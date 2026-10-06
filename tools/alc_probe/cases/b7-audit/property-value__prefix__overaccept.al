// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement prefix, 6 cells; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#prefix/comparison
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / prefix (6 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0198) but the parser is clean; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin%23prefix/comparison#0
// expect: !TPL !TPL2 !X accept
// expect: !TPL !TPL2 X accept
// expect: !TPL TPL2 !X accept
// expect: !TPL TPL2 X accept
// expect: TPL !TPL2 !X accept
// expect: TPL !TPL2 X accept
// expect: TPL TPL2 !X reject(AL0104,AL0198)
// expect: TPL TPL2 X reject(AL0104,AL0198)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#prefix/comparison in tools/b7_audit/evidence.jsonl.gz
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
                    
true =
#if X
true =
#endif
false
;
#else
                    true;
#endif
#endif
}
