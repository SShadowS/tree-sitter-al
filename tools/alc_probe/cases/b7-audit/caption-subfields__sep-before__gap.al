// B7a Task 10 witness (GAP): family caption-subfields, base placement sep-before, 72 cells; representative occ:caption_value:0.1.0.0.0.0@action_body#sep-before
// Fixture b7_gap_caption_subfields_test.txt#B7a GAP: caption-subfields / sep-before (72 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:caption_value:0.1.0.0.0.0@action_body%23sep-before#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:caption_value:0.1.0.0.0.0@action_body#sep-before in tools/b7_audit/evidence.jsonl.gz
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
                    
'a'
#if X
, Locked = true
#endif
, MaxLength = 10
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
