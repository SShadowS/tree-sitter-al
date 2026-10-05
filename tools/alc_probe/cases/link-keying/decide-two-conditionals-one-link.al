// DECIDE (two sequential conditionals forming one link value, deferred-work item 35)
// expect: * accept
// source: docs/deferred-work.md (B5b final review)
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
#endif
#if not X
        "No." = field(Name);
#endif
    } } }
}
