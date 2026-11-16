// NOT COVERED by the F2 design: the same header split outside a layout: action, action
// group, enum value, report column, query column, xmlport element.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F2)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
        field(2; N; Integer) { }
    }
}
enum 50100 E
{
#if A
    value(0; V1)
#else
    value(0; V2)
#endif
    {
        Caption = 'x';
    }
}
page 50100 P
{
    SourceTable = T;
    actions
    {
        area(Processing)
        {
#if A
            action(A1)
#else
            action(A2)
#endif
            {
                Caption = 'x';
            }
#if A
            group(G1)
#else
            group(G2)
#endif
            {
            }
        }
    }
}
report 50100 R
{
    dataset
    {
        dataitem(D; T)
        {
#if A
            column(C1; K)
#else
            column(C1; N)
#endif
            {
            }
        }
    }
}
query 50100 Q
{
    elements
    {
        dataitem(D; T)
        {
#if A
            column(C1; K)
#else
            column(C1; N)
#endif
            {
            }
        }
    }
}
xmlport 50100 X
{
    schema
    {
        textelement(Root)
        {
#if A
            textelement(E1)
#else
            textelement(E2)
#endif
            {
            }
        }
    }
}
