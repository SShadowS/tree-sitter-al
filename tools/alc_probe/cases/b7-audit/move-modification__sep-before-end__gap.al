// B7a Task 10 witness (GAP): family move-modification, base placement sep-before-end, 60 cells; representative occ:moveafter_modification:1.2@action_body#sep-before-end
// Fixture b7_gap_move_modification_test.txt#B7a GAP: move-modification / sep-before-end (60 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:moveafter_modification:1.2@action_body%23sep-before-end#0
// expect: !X reject(AL0104)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:moveafter_modification:1.2@action_body#sep-before-end in tools/b7_audit/evidence.jsonl.gz
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
            field(K; Rec.K) { }
            field(N; Rec.N) { }
            field(B; Rec.B) { }
        }
    }
    actions
    {
        area(Processing)
        {
            action(A1) { trigger OnAction() begin end; }
            action(A2) { trigger OnAction() begin end; }
            action(A3) { trigger OnAction() begin end; }
        }
    }
}
pageextension 50113 PE extends PG
{
    actions
    {
        moveafter(
A1
#if X
; A2
#endif
)
    }
}
