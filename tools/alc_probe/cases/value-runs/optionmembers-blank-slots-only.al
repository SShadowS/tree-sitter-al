// Fixture property_value_run_audit_test.txt#B11 audit: an all-`,` conditional OptionMembers run is an option_member_list since B13 keyed the name (deferred item 38; it read as a permission list before; invalid AL in every configuration, alc AL0153; pinned to detect change, not endorsed)#0
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
