// B5 host case: tableextension added field, whole-if. The host object is the fixture text in
// test/corpus/table_relation_keying_test.txt.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.2
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20]) { }
        field(2; F2; Integer) { }
    }
}
tableextension 50110 TE extends T
{
    fields
    {
        field(50110; NewF; Code[20])
        {
            TableRelation =
#if X
            Customer
#else
            Vendor."No."
#endif
            ;
        }
    }
}
