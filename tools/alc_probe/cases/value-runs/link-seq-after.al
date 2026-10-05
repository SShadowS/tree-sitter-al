// B11: SubPageLink, two groups with the `;` after the last #endif (spec 2.1, 3.1 steps 3/4/5 by family).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 2.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { part(L; CustList) {
SubPageLink =
#if X
    "No." = field("No.")
#endif
#if not X
    "No." = field(Name)
#endif
    ;
} } } }
