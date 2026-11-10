// expect: * accept
// source: deferred item 98: a shape that still ERRORs: an empty group inside an arm of a `;` group
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; "No."; Code[20])
        {
            TableRelation =
Item
#if X
#if Z
#endif
;
#else
;
#endif
        }
    }
}
