// B11: SubPageLink entirely conditional run: missing, leading and trailing separators, nothing selected.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: !W !X !Y !Z reject(AL0104,AL0107,AL0292)
// expect: !W !X Y Z reject(AL0104,AL0124,AL0224)
// expect: !W X !Y !Z reject(AL0104,AL0107,AL0292)
// expect: !W X !Y Z reject(AL0104,AL0107,AL0292)
// expect: !W X Y !Z reject(AL0104,AL0107,AL0292)
// expect: !W X Y Z reject(AL0104,AL0107,AL0224,AL0292)
// expect: W !X !Y !Z reject(AL0104,AL0107,AL0292)
// expect: W !X !Y Z reject(AL0104,AL0107,AL0292)
// expect: W !X Y !Z reject(AL0104,AL0107,AL0292)
// expect: W !X Y Z reject(AL0104,AL0124,AL0198,AL0224)
// expect: W X !Y !Z reject(AL0104,AL0107,AL0292)
// expect: W X !Y Z reject(AL0104,AL0107,AL0292)
// expect: W X Y !Z reject(AL0104,AL0107,AL0292)
// expect: W X Y Z reject(AL0104,AL0107,AL0198,AL0224,AL0292)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
page 50100 P { SourceTable = Cust; layout { area(Content) { part(L; CustList) {
SubPageLink =
#if X
    ,
#endif
#if Y
    "No." = field("No.")
#endif
#if Z
    Name = field(Name)
#endif
#if W
    ,
#endif
;
} } } }
