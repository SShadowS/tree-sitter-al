// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family link-list, base placement seed:link-keying__g11-report-dataitem-empty-arm-beside-terminated, 1 cells; representative seed:link-keying__g11-report-dataitem-empty-arm-beside-terminated
// Fixture b7_gap_link_list_test.txt#B7a REJECTED/over-accepts(syntax): link-list / seed:link-keying__g11-report-dataitem-empty-arm-beside-terminated (1 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104) but the parser is clean; representative seed:link-keying__g11-report-dataitem-empty-arm-beside-terminated#0
// expect: !X accept
// expect: X reject(AL0104)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:link-keying__g11-report-dataitem-empty-arm-beside-terminated in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
report 50130 R
{
    dataset { dataitem(C; Cust) { } dataitem(D; Cust) {
        DataItemLinkReference = C;
        DataItemLink =
#if X
#else
        Name = field(Name);
#endif
    } }
}
