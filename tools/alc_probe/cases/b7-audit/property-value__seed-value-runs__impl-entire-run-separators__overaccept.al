// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement seed:value-runs__impl-entire-run-separators, 1 cells; representative seed:value-runs__impl-entire-run-separators
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / seed:value-runs__impl-entire-run-separators (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0153,AL0301,AL0596) but the parser is clean; representative seed:value-runs__impl-entire-run-separators#0
// expect: !V !W !X !Y !Z reject(AL0153,AL0596)
// expect: !V !W !X !Y Z reject(AL0596)
// expect: !V !W !X Y !Z reject(AL0596)
// expect: !V !W !X Y Z reject(AL0104)
// expect: !V !W X !Y !Z reject(AL0107)
// expect: !V !W X !Y Z reject(AL0107)
// expect: !V !W X Y !Z reject(AL0301)
// expect: !V !W X Y Z accept
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
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__impl-entire-run-separators in tools/b7_audit/evidence.jsonl.gz
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
