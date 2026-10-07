// host: ml_value_list
// valid: !X,!Z; !X,Z
// seed-source: tools/alc_probe/cases/value-runs/captionml-after-t-suffix-empty.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture property_value_run_test.txt#B11: CaptionML `;`-after run ending in a terminated group, then an empty group and `;`: the property ends at the group (spec 3.2), the rest is body content#0
// B11 controller ruling (Task 5 review): a `;`-after run whose last group is terminated, then a directive-only empty group and `;`.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 3.2
// expect: * accept
// expect: X reject(AL0104)
table 50101 Cust { fields { field(1; A; Code[20]) { } field(2; B; Code[20]) { } } }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.A) {
CaptionML =
#if X
ENU='a'
#endif
#if not X
ENU='b';
#else
ENU='c';
#endif
#if Z
#endif
;
} } } }
