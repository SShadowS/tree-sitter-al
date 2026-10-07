// B7a Task 10 witness (GAP): family sorting, base placement elif, 18 cells; representative occ:sorting_value:0.0.3.0.0@action_body#elif
// Fixture strict_conditional_sorting_fields_test.txt#strict sorting: %23elif arm (elif)#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:sorting_value:0.0.3.0.0@action_body#elif in tools/b7_audit/evidence.jsonl.gz
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
, N
#elif Y
, "B"
#endif
, "O"
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
