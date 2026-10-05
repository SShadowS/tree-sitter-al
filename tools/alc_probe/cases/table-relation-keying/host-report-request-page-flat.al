// B5 host case: report request-page field, flat. The host object is the fixture text in
// test/corpus/table_relation_keying_test.txt.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.2
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
report 50130 R
{
    ProcessingOnly = true;
    requestpage
    {
        layout
        {
            area(Content)
            {
                field(Fx; V)
                {
                    TableRelation = Customer."No." where("No." = const('A'));
                }
            }
        }
    }
    var
        V: Code[20];
}
