// B7a Task 10 witness (GAP): family caption-subfields, base placement holes-mid, 72 cells; representative occ:caption_value:0.1.0.0.0.0@action_body#holes-mid
// Fixture strict_conditional_label_caption_tails_test.txt#B7b-1d caption / holes-mid#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0107)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:caption_value:0.1.0.0.0.0@action_body#holes-mid in tools/b7_audit/evidence.jsonl.gz
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
                    
'a' ,
#if X
,
#endif
Locked = true
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
