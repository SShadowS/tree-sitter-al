// expect: * accept
// source: deferred item 78, neighbour: a conditional if-head, then a conditional else group directly (no where), `;` inside the arms
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
#if Y
                else Customer;
#else
                else Vendor;
#endif
        }
    }
}
