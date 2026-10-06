// B7a Task 10 witness (GAP): family expression-tail, base placement unary-not, 24 cells; representative bnd:preproc_conditional_expression_tail:operand:end@action_body#unary-not/comparison
// Fixture b7_gap_expression_tail_test.txt#B7a GAP: expression-tail / unary-not (24 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:preproc_conditional_expression_tail:operand:end@action_body%23unary-not/comparison#0
// expect: !TPL !TPL3 !X accept
// expect: !TPL !TPL3 X accept
// expect: !TPL TPL3 !X accept
// expect: !TPL TPL3 X accept
// expect: TPL !TPL3 !X accept
// expect: TPL !TPL3 X accept
// expect: TPL TPL3 !X accept
// expect: TPL TPL3 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:preproc_conditional_expression_tail:operand:end@action_body#unary-not/comparison in tools/b7_audit/evidence.jsonl.gz
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
#if TPL3
                    Ok
#if TPL
and 
Ok =
#if X
not true
#else
false
#endif

#endif
                    ;
#else
                    Ok;
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
