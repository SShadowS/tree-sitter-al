// B7b-3 Phase 0 probe move/group-two-targets
// Fixture b7b3_move_args_test.txt#b7b3 move OVERACCEPT (spec 5.4): two targets in one group (group-two-targets)#0
// expect: !X reject(AL0107)
// expect: X reject(AL0104,AL0107,AL0198)
// source: B7b-3 Phase 0, 2026-10-08
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
            action(A4) { trigger OnAction() begin end; }
            action("My Action") { trigger OnAction() begin end; }
            action(Value) { trigger OnAction() begin end; }
        }
    }
}
pageextension 50113 PE extends PG
{
    actions
    {
        moveafter(
#if X
A1 , A2
#endif
; A3
)
    }
}
