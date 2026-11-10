// expect: * accept
// source: item 84: an else group after a conditional head whose other arm is only the property `;` (and its mirror, all-`;` forms)
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
;
#else
;
#endif
        }
    }
}
