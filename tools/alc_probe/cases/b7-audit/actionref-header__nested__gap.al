// B7a Task 10 witness (GAP): family actionref-header, base placement nested, 3 cells; representative occ:actionref_declaration:3@action_body#nested
// Fixture b7_gap_actionref_header_test.txt#B7a GAP: actionref-header / nested (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:actionref_declaration:3@action_body%23nested#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:actionref_declaration:3@action_body#nested in tools/b7_audit/evidence.jsonl.gz
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
            action(A1) { trigger OnAction() begin end; }
        }
        area(Promoted)
        {
            actionref(
AR
#if X
#if Y
;
#else
;
#endif
#else
;
#endif
A1
) { }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
