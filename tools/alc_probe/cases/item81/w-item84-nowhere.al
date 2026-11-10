// expect: * accept
// source: items 81/84 second review: item 84's group after a conditional if-head with no where (deferred item 99 GAP, table_relation_item99_gap_test.txt)
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
 if (A = const(1)) Item
#else
 if (A = const(2)) Resource
#endif
#if X
;
#else
else Customer;
#endif
        }
    }
}
