// host: property
// valid: X
// seed-source: tools/alc_probe/cases/value-runs/b13-caption-locked.al (verdicts measured by alc, as recorded in its expect lines)
// source: test/corpus/property_value_run_b13_gap_test.txt case 7
// B11: B13 shape: caption `'a',` then `Locked = true` across groups (step 5).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: !X reject(AL0219)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Caption =
#if X
    'a',
#endif
#if X
    Locked = true
#endif
;
} } } }
