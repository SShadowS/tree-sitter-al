// B7a Task 10 witness (GAP): family fieldgroup-header, base placement sep-only, 6 cells; representative occ:addlast_fieldgroup_modification:3@fieldgroups_body#sep-only
// Fixture b7_gap_fieldgroup_header_test.txt#B7a GAP: fieldgroup-header / sep-only (6 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:addlast_fieldgroup_modification:3@fieldgroups_body%23sep-only#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:addlast_fieldgroup_modification:3@fieldgroups_body#sep-only in tools/b7_audit/evidence.jsonl.gz
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
        addlast(
DropDown
#if X
;
#else
;
#endif
N
) { }
    }
}
