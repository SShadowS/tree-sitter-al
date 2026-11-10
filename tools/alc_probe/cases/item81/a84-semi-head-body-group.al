// expect: * accept
// source: items 81/84 review: a group of `;` arms after a head whose arms end in `;` is the body's own conditional (fixture "a ; group after a head whose arms end in ; stays the body conditional")
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
 Item;
#else
 Resource;
#endif
#if Y
;
#else
;
#endif
        }
    }
}
