// host: link_value_list
// valid: *
// seed-source: tools/alc_probe/cases/link-keying/host-query-dataitem-tablefilter-dataitemtablefilter-body-if.al (verdicts measured by alc, as recorded in its expect lines)
// B5b host x property x placement: query-dataitem-tablefilter, DataItemTableFilter, body-if.
// expect: * accept
// source: docs/superpowers/specs/2026-10-05-link-keying-design.md section 5.1/5.2
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
query 50150 Q
{
    elements { dataitem(C; Cust) {
#if X
        DataItemTableFilter = Name = const('A');
#else
        DataItemTableFilter = "No." = filter(1);
#endif
        column(No; "No.") { }
    } }
}
