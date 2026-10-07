// B7b-1 Task 2 route cardinality (spec 4.2): route sorting / declaration_body; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:sorting_value:0.0.3.0.0@declaration_body#empty-list.
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
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
    }
}
page 50102 PG
{
    SourceTable = T;
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
    layout
    {
        area(Content)
        {
            field(N; Rec.N) { }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
