// expect: * accept
// source: items 81/84: the same `;` placements inside a preproc_conditional_table_relation branch (B7a occ:_table_relation_branch)
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50104 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; "No."; Code[20])
        {
            TableRelation =
if (A = const(1)) Item else
#if TPL
Resource
#if X
;
#else
;
#endif
#else
Vendor;
#endif
        }
    }
}
