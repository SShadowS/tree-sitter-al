// host: ml_value_list
// valid: *
// seed-source: tools/alc_probe/cases/value-runs/b13-ml-conditional-terminator.al (verdicts measured by alc, as recorded in its expect lines)
// source: test/corpus/property_value_run_b13_gap_test.txt case 9
// B11: B13 shape: CaptionML with a conditional terminator, `;` inside an #else arm, then a conditional `;` (controller ruling, Task 7).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 3.1 step 5
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
CaptionML =
#if X
    ENU='a'
#else
    ENU='b';
#endif
#if X
#if Y
#endif
;
#endif
} } } }
