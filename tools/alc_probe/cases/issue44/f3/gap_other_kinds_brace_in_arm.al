// NOT COVERED by the F3 design: the same shape (header and `{` inside each arm, body after
// #endif) for a group, a usercontrol, an action, a key, an enum value.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F3)
controladdin AddInA
{
}
controladdin AddInB
{
}
enum 50100 E
{
#if A
    value(0; V1)
    {
#else
    value(0; V2)
    {
#endif
        Caption = 'x';
    }
}
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
        field(2; N; Integer) { }
    }
    keys
    {
#if A
        key(PK; K)
        {
#else
        key(PK; K, N)
        {
#endif
            Clustered = true;
        }
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
            group(G1)
            {
#else
            group(G2)
            {
#endif
                field(F; Rec.K) { }
            }
#if A
            usercontrol(U; AddInA)
            {
#else
            usercontrol(U; AddInB)
            {
#endif
            }
        }
    }
    actions
    {
        area(Processing)
        {
#if A
            action(A1)
            {
#else
            action(A2)
            {
#endif
                Caption = 'x';
            }
        }
    }
}
