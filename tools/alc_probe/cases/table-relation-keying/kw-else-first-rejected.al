// alc rejects else as a segment word.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md rev 4 (segment words); recorded by B5 Task 1, 2026-10-05
// expect: * reject(AL0107,AL0149)
table 50101 Customer { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; "Currency Code"; Code[10]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50104 "Acc. Sched. Name" { fields { field(1; Name; Code[10]) { } } }
table 50300 "Else" { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = Else."No.";
        }
        field(2; F2; Integer) { }
        field(3; "Currency Code"; Code[10]) { }
        field(4; Flag; Boolean) { }
        field(5; Flag2; Boolean) { }
    }
}
