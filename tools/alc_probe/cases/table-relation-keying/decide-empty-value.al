// DECIDE (alc 18.0.41: REJECT AL0107; the empty value is not valid, B5 Task 4 drops optional() around the keyed value):
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.1
// expect: * reject(AL0107)
table 50101 Customer { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; "Currency Code"; Code[10]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50104 "Acc. Sched. Name" { fields { field(1; Name; Code[10]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = ;
        }
        field(2; F2; Integer) { }
        field(3; "Currency Code"; Code[10]) { }
        field(4; Flag; Boolean) { }
        field(5; Flag2; Boolean) { }
    }
}
