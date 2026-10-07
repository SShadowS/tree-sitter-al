// B7a Task 10 witness (GAP): family expression-tail, base placement prefix, 8 cells; representative bnd:preproc_conditional_expression_tail:operand:end@action_body#prefix/membership
// Fixture b7_gap_expression_tail_test.txt#B7a GAP: expression-tail / prefix (8 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:preproc_conditional_expression_tail:operand:end@action_body%23prefix/membership#0
// expect: !TPL !TPL3 !X accept
// expect: !TPL !TPL3 X accept
// expect: !TPL TPL3 !X accept
// expect: !TPL TPL3 X accept
// expect: TPL !TPL3 !X accept
// expect: TPL !TPL3 X accept
// expect: TPL TPL3 !X accept
// expect: TPL TPL3 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:preproc_conditional_expression_tail:operand:end@action_body#prefix/membership in tools/b7_audit/evidence.jsonl.gz
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
Ok in
#if X
[true, false] in
#endif
[true]

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
