// B5 host case: table field, continued. The host object is the fixture text in
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
            TableRelation = if (F2 = const(1)) Customer
#if X
            else Vendor
#else
            else "G/L Account"
#endif
            ;
        }
        field(2; F2; Integer) { }
    }
}
