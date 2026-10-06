// B11: Spec 5.1 shape: first group's only arm is a nested empty group then `;`, then a SEPARATE second group (DataItemLink, report dataitem).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: X !Y reject(AL0171)
// expect: X Y reject(AL0171)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
report 50100 R { dataset { dataitem(C; Cust) { column(No; "No.") { } dataitem(D; Cust) {
DataItemLinkReference = C;
DataItemLink =
#if X
#if Y
#endif
    ;
#endif
#if not X
    "No." = field("No.");
#endif
} } } }
