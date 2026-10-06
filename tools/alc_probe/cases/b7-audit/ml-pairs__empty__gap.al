// B7a Task 10 witness (GAP): family ml-pairs, base placement empty, 27 cells; representative occ:ml_value_list:0.1.0.0@action_body#empty
// Fixture b7_gap_ml_pairs_test.txt#B7a GAP: ml-pairs / empty (27 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:ml_value_list:0.1.0.0@action_body%23empty#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:ml_value_list:0.1.0.0@action_body#empty in tools/b7_audit/evidence.jsonl.gz
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
                    
ENU = 'a' ,
#if X
#endif
DAN = 'b'
;
#else
                    ENU = 'c';
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
