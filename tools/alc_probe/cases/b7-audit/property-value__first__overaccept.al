// B7b-2 Task 12 witness (REJECTED/over-accepts(syntax)): family property-value, base placement first, 18 cells; representative bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#first/comparison
// Fixture b7b2_property_value_test.txt#B7b-2 property-value / first: moved from b7_gap_property_value_test.txt#0
// expect: !TPL !TPL2 !X accept
// expect: !TPL !TPL2 X accept
// expect: !TPL TPL2 !X accept
// expect: !TPL TPL2 X accept
// expect: TPL !TPL2 !X accept
// expect: TPL !TPL2 X accept
// expect: TPL TPL2 !X accept
// expect: TPL TPL2 X reject(AL0104,AL0198)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@preproc_conditional_controladdin#first/comparison in tools/b7_audit/evidence.jsonl.gz; the group is OVERACCEPT since B7b-2 Phase C parses the split tree clean (Task 12)
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

#if X
true =
#endif
true
;
#else
                    true;
#endif
#endif
}
