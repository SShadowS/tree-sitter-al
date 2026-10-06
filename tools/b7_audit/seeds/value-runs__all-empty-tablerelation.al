// host: table_relation_value
// valid: none
// seed-source: tools/alc_probe/cases/value-runs/all-empty-tablerelation.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture property_value_run_negative_test.txt#B11 negative: TableRelation all-empty value is an ERROR, the core is required (alc AL0107 in every configuration)#0
// B11: All-empty whole value, TableRelation: `N = #if X #endif ;` (spec 4.1).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * reject(AL0107)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
table 50100 T { fields { field(1; K; Code[20]) {
TableRelation =
#if X
#endif
;
} } }
