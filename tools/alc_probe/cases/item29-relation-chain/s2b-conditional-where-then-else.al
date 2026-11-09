// expect: * accept
// source: docs/deferred-work.md item 29, shape 2 inside an if chain (#if around the then target's where, shared else after)
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Option) { OptionMembers = X, Y; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (A = const(X)) Item
#if X
                where(A = const(1))
#endif
                else Customer;
        }
    }
}
