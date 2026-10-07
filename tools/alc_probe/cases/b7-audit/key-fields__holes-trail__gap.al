// B7a Task 10 witness (GAP): family key-fields, base placement holes-trail, 12 cells; representative occ:field_list:1.0.0@addlast_fieldgroup_modification#holes-trail
// Fixture strict_conditional_field_list_items_test.txt#strict field_list MIXED: addlast, separator-only group after the last item (holes-trail)#0
// expect: !X accept
// expect: X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:field_list:1.0.0@addlast_fieldgroup_modification#holes-trail in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
    fieldgroups
    {
        fieldgroup(DropDown; K) { }
    }
}
tableextension 50110 TE extends T
{
    fieldgroups
    {
        addlast(DropDown; 
N , B
#if X
,
#endif
) { }
    }
}
