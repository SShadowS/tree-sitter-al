// Keyword as the last segment, a field name.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.1
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; "Currency Code"; Code[10]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50104 "Acc. Sched. Name" { fields { field(1; Name; Code[10]) { } } }
table 50209 Holder { fields { field(1; "NamespacE"; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = Holder.NamespacE;
        }
        field(2; F2; Integer) { }
        field(3; "Currency Code"; Code[10]) { }
        field(4; Flag; Boolean) { }
        field(5; Flag2; Boolean) { }
    }
}
