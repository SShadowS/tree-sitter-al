// expect: * accept
// source: docs/deferred-work.md item 29, shape 1 (mid-chain #if, shared else)
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Option) { OptionMembers = X, Y, Z; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (A = const(X)) Item
#if X
                else if (A = const(Y)) Vendor
#endif
                else Customer;
        }
    }
}
