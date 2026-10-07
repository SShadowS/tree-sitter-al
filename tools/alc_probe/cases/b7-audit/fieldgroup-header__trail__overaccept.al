// B7b-1 Task 13 witness (REJECTED/over-accepts(syntax)): family fieldgroup-header, base placement trail, 3 cells; representative occ:fieldgroup_declaration:3@fieldgroups_body#trail
// Fixture strict_conditional_field_list_items_test.txt#strict field_list MIXED: fieldgroup, the first item in a group right after the fixed ; (fieldgroup-header trail)#0
// expect: !X reject(AL0107)
// expect: X accept
// source: recorded by B7b-1 Task 13, 2026-10-07: the alc split verdicts of cell occ:fieldgroup_declaration:3@fieldgroups_body#trail in tools/b7_audit/evidence.jsonl.gz
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
        fieldgroup(
Brick ;
#if X
K
#endif
, N) { }
    }
}
