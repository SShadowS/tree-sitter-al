// B11: Implementation entirely conditional run: missing, leading and trailing separators, nothing selected.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 5.1
// expect: * accept
// expect: !V !W !X !Y !Z reject(AL0153,AL0596)
// expect: !V !W !X !Y Z reject(AL0596)
// expect: !V !W !X Y !Z reject(AL0596)
// expect: !V !W !X Y Z reject(AL0104)
// expect: !V !W X !Y !Z reject(AL0107)
// expect: !V !W X !Y Z reject(AL0107)
// expect: !V !W X Y !Z reject(AL0301)
// expect: !V W !X !Y !Z reject(AL0107)
// expect: !V W !X !Y Z reject(AL0107)
// expect: !V W !X Y !Z reject(AL0107)
// expect: !V W !X Y Z reject(AL0104,AL0107)
// expect: !V W X !Y !Z reject(AL0107)
// expect: !V W X !Y Z reject(AL0107)
// expect: !V W X Y !Z reject(AL0107,AL0301)
// expect: !V W X Y Z reject(AL0107)
// expect: V !W !X !Y !Z reject(AL0107)
// expect: V !W !X !Y Z reject(AL0301)
// expect: V !W !X Y !Z reject(AL0301)
// expect: V !W !X Y Z reject(AL0104,AL0301)
// expect: V !W X !Y !Z reject(AL0107)
// expect: V !W X !Y Z reject(AL0107,AL0301)
// expect: V !W X Y !Z reject(AL0107,AL0301)
// expect: V !W X Y Z reject(AL0301)
// expect: V W !X !Y !Z reject(AL0107)
// expect: V W !X !Y Z reject(AL0107,AL0301)
// expect: V W !X Y !Z reject(AL0107,AL0301)
// expect: V W !X Y Z reject(AL0104,AL0107,AL0301)
// expect: V W X !Y !Z reject(AL0107)
// expect: V W X !Y Z reject(AL0107,AL0301)
// expect: V W X Y !Z reject(AL0107,AL0301)
// expect: V W X Y Z reject(AL0107,AL0301)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
interface IBar { procedure Baz(); }
codeunit 50108 BarImpl implements IBar { procedure Baz() begin end; }
codeunit 50109 BarImpl2 implements IBar { procedure Baz() begin end; }
enum 50105 E implements IFoo, IBar { Extensible = true; value(0; A) {
Implementation =
#if W
    ,
#endif
#if Y
    IFoo = FooImpl
#endif
#if X
    ,
#endif
#if Z
    IBar = BarImpl
#endif
#if V
    ,
#endif
;
} }
