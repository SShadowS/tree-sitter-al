// expect: * accept
// source: docs/deferred-work.md item 19, commit 824fcf4: alc four-way ACCEPT (else before the #if)
table 50101 Item { fields { field(1; "No."; Code[20]) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; Type; Option) { OptionMembers = Item, Resource; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item else
#if X
                if (Type = const(Resource)) Resource
#else
                Customer
#endif
                ;
        }
    }
}
