// B7b-1 Task 2 route cardinality (spec 4.2): route key-fields / key_declaration; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:field_list:1.0.0@key_declaration#empty-list.
// Fixture strict_conditional_field_list_items_test.txt#strict field_list MIXED: key, the whole list in one group, no %23else (empty-list)#0
// expect: !X reject(AL0306)
// expect: X accept
// source: predicted from tools/b7_audit/evidence.jsonl.gz (B7a), measured by B7b-1 Task 2, 2026-10-07
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
        key(SK; 
#if X
N , B
#endif
) { }
    }
}
