// host: property
// valid: *
// seed-source: tools/alc_probe/cases/value-runs/visible-empty-prefix.al (verdicts measured by alc, as recorded in its expect lines)
// B11: Visible, an empty `#if X #endif` before the value (spec 2.1, 3.1 step 1).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 2.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Visible =
#if X
#endif
    false;
} } } }
