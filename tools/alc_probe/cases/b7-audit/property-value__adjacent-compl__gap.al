// B7a Task 10 witness (GAP): family property-value, base placement adjacent-compl, 90 cells; representative occ:_generic_arm_t:0.3@action_body#adjacent-compl
// Fixture b7_gap_property_value_test.txt#B7a GAP: property-value / adjacent-compl (90 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_generic_arm_t:0.3@action_body%23adjacent-compl#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_generic_arm_t:0.3@action_body#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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
                Visible =
#if TPL
                    
Ok
#if X
;
#endif
#if not X
;
#endif

#else
                    not Ok;
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
