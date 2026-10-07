// B7b-1 Task 13: alc evidence of the admitted inner-list shape order-by / holes-trail, representative occ:order_by_item:3.0.0@order_by_list#holes-trail (moved from b7-audit/order-by__holes-trail__gap.al, which now witnesses the excluded outer-list GAP group)
// Fixture strict_conditional_order_by_fields_test.txt#strict order-by MIXED: separator-only group after the last item (holes-trail)#0
// expect: !X accept
// expect: X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:order_by_item:3.0.0@order_by_list#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
K , N
#if X
,
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
