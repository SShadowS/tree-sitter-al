// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family link-list, base placement seed:link-keying__g11-page-part-independent-no-else, 1 cells; representative seed:link-keying__g11-page-part-independent-no-else
// Fixture b7_gap_link_list_test.txt#B7a REJECTED/over-accepts(syntax): link-list / seed:link-keying__g11-page-part-independent-no-else (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0292) but the parser is clean; representative seed:link-keying__g11-page-part-independent-no-else#0
// expect: !X !Y reject(AL0104,AL0107,AL0292)
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:link-keying__g11-page-part-independent-no-else in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
page 50100 P
{
    SourceTable = Cust;
    layout { area(Content) { part(L; CustList) {
        SubPageLink =
#if X
        "No." = field("No.");
#elif Y
        Name = field(Name);
#endif
    } } }
}
