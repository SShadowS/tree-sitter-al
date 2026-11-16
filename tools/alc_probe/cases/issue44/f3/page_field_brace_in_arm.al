// The issue's shape for a PAGE field: header and `{` inside each arm, the body after #endif;
// with an arm-local property, and with three arms.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F3)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
        field(2; N; Integer) { }
    }
}
page 50100 P
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
#if A
            field(F; Rec.K)
            {
#else
            field(F; Rec.N)
            {
#endif
                ApplicationArea = All;
            }
#if A
            field(F2; Rec.K)
            {
                Caption = 'a';
#elif B
            field(F2; Rec.N)
            {
#else
            field(F3; Rec.N)
            {
                Caption = 'c';
#endif
                ApplicationArea = All;

                trigger OnValidate()
                begin
                end;
            }
        }
    }
}
