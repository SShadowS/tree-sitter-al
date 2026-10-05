// B11: Configuration-dependent boundary, `;`-after mixed placement (spec 9 round 1).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { field(F; Rec.Flag) {
Visible =
#if X
    true;
#else
    false
#endif
#if X
    Caption = 'x'
#endif
;
} } } }
