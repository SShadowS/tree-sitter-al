// host: table_relation_value
// valid: *
// seed-source: tools/alc_probe/cases/g11-item19-relation/else_split_semicolon_after.al (verdicts measured by alc, as recorded in its expect lines)
// expect: * accept
// source: docs/deferred-work.md item 19, commit 824fcf4: alc four-way ACCEPT (the #if/#else form)
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
            TableRelation = if (Type = const(Item)) Item
#if X
                else Resource
#else
                else Customer
#endif
                ;
        }
    }
}
