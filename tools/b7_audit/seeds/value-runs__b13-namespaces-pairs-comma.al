// host: namespace_value_list
// valid: *
// seed-source: tools/alc_probe/cases/value-runs/b13-namespaces-pairs-comma.al (verdicts measured by alc, as recorded in its expect lines)
// source: test/corpus/property_value_run_b13_gap_test.txt case 6
// B11: B13 shape: Namespaces pairs joined by `,` across groups (step 5).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
xmlport 50100 X {
Namespaces =
#if X
    a = 'u',
#endif
#if X
    b = 'v'
#endif
;
schema { textelement(R) { } } }
