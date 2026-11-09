// expect: * accept
// source: docs/deferred-work.md item 29, shape 2 (#if around the where tail)
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; "No."; Code[20])
        {
            TableRelation = Customer
#if X
                where(A = const(1))
#endif
                ;
        }
    }
}
