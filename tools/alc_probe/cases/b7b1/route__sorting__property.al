// B7b-1 Task 2 route cardinality (spec 4.2): route sorting / property; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:sorting_value:0.0.3.0.0@property#empty-list.
// expect: !X accept
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
    }
}
page 50102 PG
{
    SourceTable = T;
    SourceTableView = sorting(
#if X
K , N
#endif
);
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
