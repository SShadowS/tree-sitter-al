// B7a Task 10 witness (GAP): family ml-pairs, base placement trail, 99 cells; representative occ:_ml_arm_t:0.3@action_body#trail
// Fixture b7_gap_ml_pairs_test.txt#B7a GAP: ml-pairs / trail (99 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_ml_arm_t:0.3@action_body%23trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0104)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_ml_arm_t:0.3@action_body#trail in tools/b7_audit/evidence.jsonl.gz
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
                CaptionML =
#if TPL
                    
ENU = 'a'
#if X
;
#endif

#else
                    ENU = 'b';
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
