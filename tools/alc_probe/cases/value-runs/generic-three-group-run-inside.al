// Fixture property_value_run_test.txt#B11: generic Caption, three groups, `;` inside (step 2)#0
// B11: Generic Caption, three groups, `;` inside every arm (step 2).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: !X !Y !Z reject(AL0104,AL0219)
// expect: !X Y Z reject(AL0104,AL0198)
// expect: X !Y Z reject(AL0104,AL0198)
// expect: X Y !Z reject(AL0104,AL0198)
// expect: X Y Z reject(AL0104,AL0198)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Caption =
#if X
    'a';
#endif
#if Y
    'b';
#endif
#if Z
    'c';
#endif
} } } }
