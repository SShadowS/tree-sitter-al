// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family unary-operand, base placement op-only, 7 cells; representative bnd:unary_expression:operand:end@property_expression#op-only/comparison
// Fixture b7_gap_unary_operand_test.txt#B7a REJECTED/over-accepts(syntax): unary-operand / op-only (7 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0198) but the parser is clean; representative bnd:unary_expression:operand:end@property_expression%23op-only/comparison#0
// expect: !X reject(AL0104,AL0198)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:unary_expression:operand:end@property_expression#op-only/comparison in tools/b7_audit/evidence.jsonl.gz
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
            field(N; Rec.N)
            {
                Visible = not 
Ok
#if X
=
#endif
true
;
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
