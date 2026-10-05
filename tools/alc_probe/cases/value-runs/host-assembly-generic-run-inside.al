// B11: Generic `;`-inside run at the assembly host (spec 4.4).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
dotnet { assembly(mscorlib) {
Version =
#if X
    '1.0.0.0';
#endif
#if not X
    '2.0.0.0';
#endif
Culture = 'neutral'; PublicKeyToken = 'b77a5c561934e089'; type(System.DateTime; MyDateTime) { } } }
