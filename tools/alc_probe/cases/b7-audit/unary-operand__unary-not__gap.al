// B7a Task 10 witness (GAP): family unary-operand, base placement unary-not, 3 cells; representative bnd:unary_expression:operand:end@property_expression#unary-not/comparison
// Fixture b7_gap_unary_operand_test.txt#B7a GAP: unary-operand / unary-not (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:unary_expression:operand:end@property_expression%23unary-not/comparison#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:unary_expression:operand:end@property_expression#unary-not/comparison in tools/b7_audit/evidence.jsonl.gz
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
Ok =
#if X
not true
#else
false
#endif
;
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
