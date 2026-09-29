// expect: * accept
// source: docs/bc29-parse-gaps.md family E (ACCEPT in both configs), commit 42aaf7b
table 50100 Tbl { fields { field(1; A; Integer) { } field(2; B; Integer) { } } }
page 50100 Pg
{
    SourceTable = Tbl;
    layout { area(Content) { group(G) { field(A; Rec.A) { } } group(H) { field(B; Rec.B) { } } } }
    actions { area(Processing) { action(X) { trigger OnAction() begin end; } action(Y) { trigger OnAction() begin end; } } }
}
pageextension 50101 PgExt extends Pg
{
    actions
    {
#if not C27
        modify(X)
#else
        modify(Y)
#endif
        {
            Caption = 'C';
        }
    }
}
