// B7a Task 10 witness (GAP): family order-by, base placement one-elem, 3 cells; representative occ:order_by_item:3.0.0@order_by_list#one-elem
// Fixture b7_gap_order_by_test.txt#B7a GAP: order-by / one-elem (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:order_by_item:3.0.0@order_by_list%23one-elem#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:order_by_item:3.0.0@order_by_list#one-elem in tools/b7_audit/evidence.jsonl.gz
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
    OrderBy = ascending(
#if X
K , N
#else
K
#endif
);
    elements
    {
        dataitem(D; T)
        {
            column(K; K) { }
            column(N; N) { }
            filter(F; B) { }
        }
    }
}
