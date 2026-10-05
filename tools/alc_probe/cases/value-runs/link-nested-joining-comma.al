// B11: SubPageLink, a nested group carrying the joining `,` (spec 9 round 4, finding 3).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: X !Y reject(AL0104,AL0124,AL0224)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { part(L; CustList) {
SubPageLink =
    "No." = field("No.")
#if X
#if Y
    ,
#endif
    Name = field(Name)
#endif
;
} } } }
