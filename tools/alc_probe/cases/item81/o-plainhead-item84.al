// expect: * accept
// expect: !X reject(AL0149)
// source: items 81/84 second review: item 84's group after a conditional head that cannot take an else (Item / Resource): clean, alc rejects X undefined (over-acceptance, deferred item 44; main already accepts an all-else group here)
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
#if T
 Item
#else
 Resource
#endif
 where(A = const(1))
#if X
;
#else
else Customer;
#endif
        }
    }
}
