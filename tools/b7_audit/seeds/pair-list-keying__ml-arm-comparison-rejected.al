// host: ml_value_list
// valid: none
// seed-source: tools/alc_probe/cases/pair-list-keying/ml-arm-comparison-rejected.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture pair_list_property_keying_negative_test.txt#B4 negative: a keyed whole-value %23if arm holding a comparison (AL0104, AL0219)#0
// A keyed whole-value #if whose arms hold comparisons, not pairs: ERRORs inside the arms.
// expect: * reject(AL0104,AL0219)
// source: B4 Task 3, spec 2026-10-01-pair-list-property-keying-design.md §3.3
table 50100 T
{
    CaptionML =
#if X
        A = 1
#else
        B = 2
#endif
        ;
    fields { field(1; F; Integer) { } }
}
