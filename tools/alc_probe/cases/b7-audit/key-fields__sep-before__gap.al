// B7a Task 10 witness (GAP): family key-fields, base placement sep-before, 12 cells; representative occ:field_list:1.0.0@addlast_fieldgroup_modification#sep-before
// Fixture strict_conditional_field_list_items_test.txt#strict field_list: addlast, group with the separator before its item, then an item (sep-before)#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:field_list:1.0.0@addlast_fieldgroup_modification#sep-before in tools/b7_audit/evidence.jsonl.gz
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
N
#if X
, B
#endif
, "K"
) { }
    }
}
