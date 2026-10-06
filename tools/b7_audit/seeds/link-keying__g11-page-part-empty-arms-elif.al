// host: link_value_list
// valid: !X,!Y
// seed-source: tools/alc_probe/cases/link-keying/g11-page-part-empty-arms-elif.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture link_keying_test.txt#G11 empty-arms-elif, page-part (probe g11-page-part-empty-arms-elif.al): two leading absent arms, one whole value#0
// G11 shape empty-arms-elif (two leading absent arms, then a terminated #else arm), page-part (B5b Task 3).
// expect: * reject(AL0104,AL0107,AL0292)
// expect: !X !Y accept
// source: recorded by B5b Task 3, 2026-10-05
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
page 50100 P
{
    SourceTable = Cust;
    layout { area(Content) { part(L; CustList) {
        SubPageLink =
#if X
#elif Y
#else
        Name = field(Name);
#endif
    } } }
}
