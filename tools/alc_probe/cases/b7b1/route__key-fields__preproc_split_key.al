// B7b-1 Task 2 route cardinality (spec 4.2): route key-fields / preproc_split_key; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:field_list:1.0.0@preproc_split_key#empty-list.
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0306)
// expect: TPL X accept
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
#if TPL
        key(SK; 
#if X
N , B
#endif
)
#else
        key(SK; N)
#endif
        {
        }
    }
}
