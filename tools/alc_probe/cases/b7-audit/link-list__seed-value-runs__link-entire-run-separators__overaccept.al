// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family link-list, base placement seed:value-runs__link-entire-run-separators, 1 cells; representative seed:value-runs__link-entire-run-separators
// Fixture b7_gap_link_list_test.txt#B7a REJECTED/over-accepts(syntax): link-list / seed:value-runs__link-entire-run-separators (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0124,AL0198,AL0224,AL0292) but the parser is clean; representative seed:value-runs__link-entire-run-separators#0
// expect: !W !X !Y !Z reject(AL0104,AL0107,AL0292)
// expect: !W !X !Y Z accept
// expect: !W !X Y !Z accept
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
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__link-entire-run-separators in tools/b7_audit/evidence.jsonl.gz
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
