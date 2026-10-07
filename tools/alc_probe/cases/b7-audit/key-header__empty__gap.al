// B7a Task 10 witness (GAP): family key-header, base placement empty, 3 cells; representative occ:_key_header:3@key_declaration#empty
// Fixture strict_conditional_field_list_items_test.txt#strict field_list: key, empty group right after the fixed ; (key-header empty)#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_key_header:3@key_declaration#empty in tools/b7_audit/evidence.jsonl.gz
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
        key(
SK ;
#if X
#endif
N
) { }
    }
}
