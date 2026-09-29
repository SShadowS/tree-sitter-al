// expect: * accept
// source: docs/bc29-parse-gaps.md family H (ACCEPT x2), commit 9fd9a9c
table 50100 Tbl { fields { field(1; A; Integer) { } field(2; B; Integer) { } field(3; C; Integer) { } } }
page 50100 Pg
{
    SourceTable = Tbl;
    layout
    {
        area(Content)
        {
            group(G)
            {
                field(A; Rec.A) { }
#if not C28
            }
            group(R)
            {
                Caption = 'R';
                field(B; Rec.B) { }
#endif
                field(C; Rec.C) { }
            }
        }
    }
}
