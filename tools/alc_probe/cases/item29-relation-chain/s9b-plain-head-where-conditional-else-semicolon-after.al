// expect: * accept
// source: deferred item 78, neighbour: s9 with the `;` after #endif
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50104 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; "No."; Code[20])
        {
            TableRelation = if (A = const(1)) Item where(A = const(1))
#if Y
                else Customer
#else
                else Vendor
#endif
                ;
        }
    }
}
