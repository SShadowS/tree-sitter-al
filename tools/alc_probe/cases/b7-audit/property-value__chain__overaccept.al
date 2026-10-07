// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement chain, 2 cells; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#chain/logical
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / chain (2 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0124) but the parser is clean; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin%23chain/logical#0
// expect: !TPL !TPL2 !X accept
// expect: !TPL !TPL2 X accept
// expect: !TPL TPL2 !X accept
// expect: !TPL TPL2 X accept
// expect: TPL !TPL2 !X accept
// expect: TPL !TPL2 X accept
// expect: TPL TPL2 !X reject(AL0104,AL0124)
// expect: TPL TPL2 X reject(AL0104,AL0124)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#chain/logical in tools/b7_audit/evidence.jsonl.gz
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
                    
true or true
#if X
and false
#endif
or Ok
;
#else
                    true;
#endif
#endif
}
