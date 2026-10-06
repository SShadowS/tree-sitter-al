// host: link_value_list
// valid: *
// seed-source: tools/alc_probe/cases/link-keying/host-page-action-runpagelink-semi-after.al (verdicts measured by alc, as recorded in its expect lines)
// B5b host x property x placement: page-action, RunPageLink, semi-after.
// expect: * accept
// source: docs/superpowers/specs/2026-10-05-link-keying-design.md section 5.1/5.2
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
page 50100 P
{
    SourceTable = Cust;
    actions { area(Processing) { action(A) {
        RunObject = page CustCard;
        RunPageLink =
#if X
        "No." = field("No.")
#else
        Name = field(Name)
#endif
        ;
    } } }
}
