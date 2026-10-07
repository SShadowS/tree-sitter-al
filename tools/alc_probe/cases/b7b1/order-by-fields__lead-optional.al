// B7b-1 Task 13: alc evidence of the admitted inner-list shape order-by / lead-optional, representative occ:order_by_item:3.0.0@order_by_list#lead-optional (moved from b7-audit/order-by__lead-optional__gap.al, which now witnesses the excluded outer-list GAP group)
// Fixture strict_conditional_order_by_fields_test.txt#strict order-by: leading group whose arm ends with the separator (lead-optional)#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:order_by_item:3.0.0@order_by_list#lead-optional in tools/b7_audit/evidence.jsonl.gz
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
K ,
#endif
N
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
