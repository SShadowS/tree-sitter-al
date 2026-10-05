// Fixture link_keying_test.txt#G11 empty-arm-beside-terminated, report-dataitem (probe g11-report-dataitem-empty-arm-beside-terminated.al) is one property#0
// G11 shape empty-arm-beside-terminated, delegate-valid pairs, report-dataitem (B5b 5.1).
// expect: * accept
// expect: !X accept
// expect: X reject(AL0104)
// source: docs/superpowers/specs/2026-10-05-link-keying-design.md section 5.1/5.2
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
