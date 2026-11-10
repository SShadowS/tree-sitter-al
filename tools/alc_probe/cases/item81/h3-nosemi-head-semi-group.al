// expect: * accept
// source: deferred item 98: a group of `;` arms after a conditional head whose arms have no `;` and no where; ERRORs
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
#if Y
;
#else
;
#endif
        }
    }
}
