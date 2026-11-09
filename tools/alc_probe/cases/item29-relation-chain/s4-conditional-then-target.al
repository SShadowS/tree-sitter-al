// expect: * accept
// source: docs/deferred-work.md item 29, shape 4 (#if around the target after an if condition)
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Option) { OptionMembers = X, Y; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (A = const(X))
#if X
                Item
#else
                Vendor
#endif
                ;
        }
    }
}
