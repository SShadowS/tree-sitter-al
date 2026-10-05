// B5 host case: table field, whole property inside a field-body #if/#else. The host object is the fixture text in
// test/corpus/table_relation_keying_test.txt.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.2
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50105 T2
{
    fields
    {
        field(1; F; Code[20])
        {
#if X
            TableRelation = Customer;
#else
            TableRelation = Vendor where("No." = const('A'));
#endif
        }
        field(2; F2; Integer) { }
    }
}
