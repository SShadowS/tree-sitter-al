// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family property-value, base placement op-only, 54 cells; representative bnd:_property_value_with_split:0.0:end@action_body#op-only/comparison
// Fixture b7_gap_property_value_test.txt#B7a REJECTED/over-accepts(syntax): property-value / op-only (54 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0198) but the parser is clean; representative bnd:_property_value_with_split:0.0:end@action_body%23op-only/comparison#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0104,AL0198)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@action_body#op-only/comparison in tools/b7_audit/evidence.jsonl.gz
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
=
#endif
true
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
