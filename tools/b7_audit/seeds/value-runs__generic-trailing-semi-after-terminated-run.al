// host: property
// valid: *
// seed-source: tools/alc_probe/cases/value-runs/generic-trailing-semi-after-terminated-run.al (verdicts measured by alc, as recorded in its expect lines)
// B11: SourceTableView, terminated run followed by a standalone `;` (step 2, the `;` after is the property's own).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust;
SourceTableView =
#if X
    where(Amount = const(1));
#endif
#if not X
    where(Amount = const(2));
#endif
;
layout { area(Content) { field(F; Rec.Flag) { } } } }
