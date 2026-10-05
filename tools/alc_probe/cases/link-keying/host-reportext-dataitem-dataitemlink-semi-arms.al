// B5b host x property x placement: reportext-dataitem, DataItemLink, semi-arms.
// expect: * accept
// source: docs/superpowers/specs/2026-10-05-link-keying-design.md section 5.1/5.2
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
report 50130 R
{
    dataset { dataitem(C; Cust) { } }
}
reportextension 50131 RE extends R
{
    dataset { addlast(C) { dataitem(D; Cust) {
        DataItemLinkReference = C;
        DataItemLink =
#if X
        "No." = field("No.");
#else
        Name = field(Name);
#endif
    } } }
}
