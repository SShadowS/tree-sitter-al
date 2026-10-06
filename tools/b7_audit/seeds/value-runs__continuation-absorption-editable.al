// host: property
// valid: X,!Y; X,Y
// seed-source: tools/alc_probe/cases/value-runs/continuation-absorption-editable.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture property_value_run_review_test.txt#B11 one-reading (spec 3.4): a non-terminated `;`-inside group then a conditional property is read as a continuation, the chosen one-reading, NOT the X=1,Y=1 tree (two properties)#0
// B11: a non-terminated `;`-inside group, then a conditional block whose arm also parses as a
// property (`Editable = false;`). The grammar reads it as a continuation of the value (spec 3.4,
// the chosen one-reading); alc reads each configuration flat.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 3.4
// expect: * accept
// expect: !X !Y reject(AL0104,AL0219)
// expect: !X Y reject(AL0219)
// source: recorded by B11 final review fix, 2026-10-06
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(4; Flag; Boolean) { } } }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Caption =
#if X
    'a';
#endif
#if Y
    Editable = false;
#endif
} } } }
