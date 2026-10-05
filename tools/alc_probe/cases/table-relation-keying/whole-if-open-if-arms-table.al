// Whole-value #if whose arms are if-relations with no else tail, the ; after #endif. (table field)
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.2 (Task 4 review minor)
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation =
#if X
            if (F2 = const(1)) Customer
#else
            if (F2 = const(2)) Vendor
#endif
            ;
        }
        field(2; F2; Integer) { }
    }
}
