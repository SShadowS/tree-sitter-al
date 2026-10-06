// host: ml_value_list
// valid: none
// seed-source: tools/alc_probe/cases/pair-list-keying/ml-arm-trailing-comma-rejected.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture pair_list_property_keying_negative_test.txt#B4 negative: a keyed whole-value %23if arm with a trailing comma (AL0301)#0
// A keyed whole-value #if whose arms end in a trailing comma: ERRORs inside the arms.
// The `;` sits in each arm: with it after #endif, recovery from the comma before #endif escapes the property.
// expect: * reject(AL0301)
// source: B4 Task 3, spec 2026-10-01-pair-list-property-keying-design.md §3.3
table 50100 T
{
    CaptionML =
#if X
        ENU='a',;
#else
        ENU='b',;
#endif
    fields { field(1; F; Integer) { } }
}
