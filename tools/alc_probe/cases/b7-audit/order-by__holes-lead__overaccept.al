// B7b-1 Task 13 witness (REJECTED/over-accepts(syntax)): family order-by, base placement holes-lead, 3 cells; representative occ:order_by_item:3.0.0@order_by_list#holes-lead (the B7a GAP witness of this shape, renamed: the strict list parses every configuration, alc still rejects one)
// Fixture strict_conditional_order_by_fields_test.txt#strict order-by MIXED: separator-only group before the first item (holes-lead)#0
// expect: !X accept
// expect: X reject(AL0107)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:order_by_item:3.0.0@order_by_list#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
,
#endif
K , N
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
