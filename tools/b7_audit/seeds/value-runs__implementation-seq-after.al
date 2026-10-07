// host: implementation_value
// valid: *
// seed-source: tools/alc_probe/cases/value-runs/implementation-seq-after.al (verdicts measured by alc, as recorded in its expect lines)
// B11: Implementation, two groups with the `;` after the last #endif (spec 2.1, 3.1 steps 3/4/5 by family).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 2.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
enum 50105 E implements IFoo { Extensible = true; value(0; A) {
Implementation =
#if X
    IFoo = FooImpl
#endif
#if not X
    IFoo = FooImpl2
#endif
    ;
} }
