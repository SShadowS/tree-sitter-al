// expect: * accept
// source: docs/bc29-parse-gaps.md family E (ACCEPT in both configs); the EDocumentDE shape, still deferred (docs/deferred-work.md item 10)
table 50100 Tbl { fields { field(1; A; Integer) { } field(2; B; Integer) { } } }
page 50100 Pg
{
    SourceTable = Tbl;
    layout { area(Content) { group(G) { field(A; Rec.A) { } } group(H) { field(B; Rec.B) { } } } }
    actions { area(Processing) { action(X) { trigger OnAction() begin end; } action(Y) { trigger OnAction() begin end; } } }
}
pageextension 50101 PgExt extends Pg
{
    layout
    {
#if not C27
        addafter(G)
        {
            group(Export)
            {
                Caption = 'E';
#else
        addlast(H)
        {
            group(BuyerReference)
            {
                ShowCaption = false;
#endif
                field(F; Rec.A) { Caption = 'F'; }
            }
        }
    }
}
