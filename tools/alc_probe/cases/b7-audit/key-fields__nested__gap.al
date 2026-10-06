// B7a Task 10 witness (GAP): family key-fields, base placement nested, 12 cells; representative occ:field_list:1.0.0@addlast_fieldgroup_modification#nested
// Fixture b7_gap_key_fields_test.txt#B7a GAP: key-fields / nested (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:field_list:1.0.0@addlast_fieldgroup_modification%23nested#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:field_list:1.0.0@addlast_fieldgroup_modification#nested in tools/b7_audit/evidence.jsonl.gz
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
#if Y
, "K"
#endif
#endif
, "O"
) { }
    }
}
