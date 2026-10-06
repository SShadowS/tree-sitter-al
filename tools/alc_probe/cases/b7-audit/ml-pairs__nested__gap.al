// B7a Task 10 witness (GAP): family ml-pairs, base placement nested, 99 cells; representative occ:_ml_arm_t:0.3@action_body#nested
// Fixture b7_gap_ml_pairs_test.txt#B7a GAP: ml-pairs / nested (99 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_ml_arm_t:0.3@action_body%23nested#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_ml_arm_t:0.3@action_body#nested in tools/b7_audit/evidence.jsonl.gz
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
#if Y
;
#else
;
#endif
#else
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
