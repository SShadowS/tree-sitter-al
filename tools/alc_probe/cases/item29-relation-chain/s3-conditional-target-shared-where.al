// expect: * accept
// source: docs/deferred-work.md item 29, shape 3 (#if around the target, shared where tail)
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
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
                where(A = const(1));
        }
    }
}
