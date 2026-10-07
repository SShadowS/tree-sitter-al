// B7a Task 10 witness (GAP): family property-terminator, base placement adjacent-compl, 150 cells; representative occ:property:0.3@declaration_body#adjacent-compl
// Fixture b7_gap_property_terminator_test.txt#B7a GAP: property-terminator / adjacent-compl (150 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:property:0.3@declaration_body%23adjacent-compl#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:property:0.3@declaration_body#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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
                
Visible = Ok
#if X
;
#endif
#if not X
;
#endif

            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
