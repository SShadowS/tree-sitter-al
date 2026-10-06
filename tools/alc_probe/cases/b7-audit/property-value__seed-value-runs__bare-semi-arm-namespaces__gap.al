// B7a Task 10 witness (GAP): family property-value, base placement seed:value-runs__bare-semi-arm-namespaces, 1 cells; representative seed:value-runs__bare-semi-arm-namespaces
// Fixture b7_gap_property_value_test.txt#B7a GAP: property-value / seed:value-runs__bare-semi-arm-namespaces (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:value-runs__bare-semi-arm-namespaces#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__bare-semi-arm-namespaces in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
xmlport 50100 X {
Namespaces =
#if X
    ;
#else
    a = 'u';
#endif
schema { textelement(R) { } } }
