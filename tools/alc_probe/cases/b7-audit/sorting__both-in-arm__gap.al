// B7a Task 10 witness (GAP): family sorting, base placement both-in-arm, 18 cells; representative occ:sorting_value:0.0.3.0.0@action_body#both-in-arm
// Fixture b7_gap_sorting_test.txt#B7a GAP: sorting / both-in-arm (18 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:sorting_value:0.0.3.0.0@action_body%23both-in-arm#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:sorting_value:0.0.3.0.0@action_body#both-in-arm in tools/b7_audit/evidence.jsonl.gz
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
, N ,
#else
,
#endif
"B"
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
