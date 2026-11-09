// expect: * reject(AL0149)
// source: deferred item 75: the item-75 tail after a conditional head of plain targets is an else without an if
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
                Item
#else
                Resource
#endif
                where(A = const(1)) else Customer;
        }
    }
}
