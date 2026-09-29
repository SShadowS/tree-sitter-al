// Negative control: two controls with no comma.
// expect: * reject
// source: docs/bc29-parse-gaps.md family A negative control (moveafter(A; C B) gives AL0104)
table 50100 Tbl { fields { field(1; A; Integer) { } field(2; B; Integer) { } field(3; C; Integer) { } } }
page 50100 Pg
{
    SourceTable = Tbl;
    layout { area(Content) { group(G) { field(A; Rec.A) { } field(B; Rec.B) { } field(C; Rec.C) { } } } }
    actions { area(Processing) { action(X) { trigger OnAction() begin end; } action(Y) { trigger OnAction() begin end; } action(Z) { trigger OnAction() begin end; } } }
}
pageextension 50101 PgExt extends Pg
{
    layout
    {
        moveafter(A; C B)
    }
}
