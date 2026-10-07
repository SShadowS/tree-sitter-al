// B7b-1 Task 2 route cardinality (spec 4.2): route sorting / preproc_conditional_xmlport; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:sorting_value:0.0.3.0.0@preproc_conditional_xmlport#empty-list.
// expect: !TPL !TPL2 !X accept
// expect: !TPL !TPL2 X accept
// expect: !TPL TPL2 !X accept
// expect: !TPL TPL2 X accept
// expect: TPL !TPL2 !X accept
// expect: TPL !TPL2 X accept
// expect: TPL TPL2 !X accept
// expect: TPL TPL2 X accept
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
    }
}
xmlport 50107 Xp
{
    schema
    {
        textelement(Root)
        {
            tableelement(D; T)
            {
#if TPL2
    SourceTableView =
#if TPL
        sorting(
#if X
K , N
#endif
);
#else
        sorting(K);
#endif
#endif
                fieldattribute(K; D.K) { }
                fieldelement(N; D.N) { }
            }
        }
    }
}
