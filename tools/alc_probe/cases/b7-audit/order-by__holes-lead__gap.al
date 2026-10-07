// B7b-1 Task 13 witness (GAP): family order-by, base placement holes-lead, 9 cells; representative occ:order_by_list:0.1.0.0@declaration_body#holes-lead
// Fixture b7_gap_order_by_test.txt#B7a GAP: order-by / holes-lead (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:order_by_list:0.1.0.0@declaration_body%23holes-lead#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0107)
// source: recorded by B7b-1 Task 13, 2026-10-07: the alc split verdicts of cell occ:order_by_list:0.1.0.0@declaration_body#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
    OrderBy =
#if TPL
        
#if X
,
#endif
ascending(K) , descending(N)
;
#else
        ascending(K);
#endif
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
