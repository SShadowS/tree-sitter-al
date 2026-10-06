// host: option_member_list
// valid: none
// seed-source: tools/alc_probe/cases/value-runs/optionmembers-blank-slots-only.al (verdicts measured by alc, as recorded in its expect lines)
// source: docs/deferred-work.md item 38
// Fixture property_value_run_audit_test.txt#B11 audit: prec.dynamic(-1) keeps the pre-B11 reading of an all-`,` conditional run (OptionMembers here is invalid AL in every configuration, alc AL0153; the permission-list reading is pre-existing, pinned to detect change, not endorsed)#0
// B11: OptionMembers entirely conditional run where some configurations select only blank slots (spec 5.1).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * reject(AL0153)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
    ,
#endif
#if Y
    ,
#endif
;
} } }
