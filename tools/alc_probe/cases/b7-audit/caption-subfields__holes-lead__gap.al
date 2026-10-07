// B7a Task 10 witness (GAP): family caption-subfields, base placement holes-lead, 72 cells; representative occ:caption_value:0.1.0.0.0.0@action_body#holes-lead
// Fixture b7_gap_caption_subfields_test.txt#B7a GAP: caption-subfields / holes-lead (72 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:caption_value:0.1.0.0.0.0@action_body%23holes-lead#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0107,AL0219)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:caption_value:0.1.0.0.0.0@action_body#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
                Caption =
#if TPL
                    
#if X
,
#endif
'a' , Locked = true
;
#else
                    'b';
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
