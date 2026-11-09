// expect: * accept
// source: deferred item 75 (split from item 29's review): a conditional head of two if-relations, then a shared where and a shared else
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
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
                where(A = const(1)) else Customer;
        }
    }
}
