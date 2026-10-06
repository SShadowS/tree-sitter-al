// B7a Task 10 witness (GAP): family column-header, base placement trail, 15 cells; representative occ:query_column:2.0.1@query_body#trail
// Fixture b7_gap_column_header_test.txt#B7a GAP: column-header / trail (15 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:query_column:2.0.1@query_body%23trail#0
// expect: !X reject(AL0107)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:query_column:2.0.1@query_body#trail in tools/b7_audit/evidence.jsonl.gz
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
query 50105 Qy
{
    elements
    {
        dataitem(D; T)
        {
            column(K; K) { }
            column(
N ;
#if X
N
#endif
) { }
            filter(F; B) { }
        }
    }
}
