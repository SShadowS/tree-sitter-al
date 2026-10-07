// B7a Task 10 witness (GAP): family sorting, base placement sep-only, 18 cells; representative occ:sorting_value:0.0.3.0.0@action_body#sep-only
// Fixture b7_gap_sorting_test.txt#B7a GAP: sorting / sep-only (18 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:sorting_value:0.0.3.0.0@action_body%23sep-only#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:sorting_value:0.0.3.0.0@action_body#sep-only in tools/b7_audit/evidence.jsonl.gz
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
    layout
    {
        area(Content)
        {
            field(N; Rec.N) { }
        }
    }
    actions
    {
        area(Processing)
        {
            action(A1)
            {
                RunObject = page PG;
                RunPageView =
#if TPL
                    sorting(
K
#if X
,
#else
,
#endif
N
);
#else
                    sorting(K);
#endif
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
