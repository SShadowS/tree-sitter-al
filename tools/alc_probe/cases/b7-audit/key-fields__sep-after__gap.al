// B7a Task 10 witness (GAP): family key-fields, base placement sep-after, 12 cells; representative occ:field_list:1.0.0@addlast_fieldgroup_modification#sep-after
// Fixture b7_gap_key_fields_test.txt#B7a GAP: key-fields / sep-after (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:field_list:1.0.0@addlast_fieldgroup_modification%23sep-after#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:field_list:1.0.0@addlast_fieldgroup_modification#sep-after in tools/b7_audit/evidence.jsonl.gz
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
N ,
#if X
B ,
#endif
"K"
) { }
    }
}
