// host: link_value_list
// valid: !X
// seed-source: tools/alc_probe/cases/value-runs/bare-semi-arm-link.al (verdicts measured by alc, as recorded in its expect lines)
// B11: Bare `;` arm, SubPageLink: `N = #if X ; #else v; #endif` (spec 3, Bare `;` arms).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: X reject(AL0104,AL0107,AL0292)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { part(L; CustList) {
SubPageLink =
#if X
    ;
#else
    "No." = field("No.");
#endif
} } } }
