// expect: * accept
// source: deferred item 81 (found by item 78's B7a cells, placement `empty`): an empty #if group between an else-group arm's relation and its `;`
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50104 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; "No."; Code[20])
        {
            TableRelation =
#if X
                if (A = const(1)) Item
#else
                if (A = const(2)) Resource
#endif
                where(A = const(1))
#if Y
                else Customer
#if Z
#endif
                ;
#else
                else Vendor;
#endif
        }
    }
}
