// The usercontrol header split for the other `kind(Name; Source) { }` controls: a part, a
// systempart, and a group choosing between two KINDS (part / usercontrol).
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F2)
controladdin AddInA
{
}
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }
}
page 50101 Sub
{
    PageType = ListPart;
    SourceTable = T;
}
page 50102 Sub2
{
    PageType = ListPart;
    SourceTable = T;
}
page 50100 P
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
#if A
            part(P1; Sub)
#else
            part(P1; Sub2)
#endif
            {
            }
#if A
            part(P2; Sub)
#else
            usercontrol(P2; AddInA)
#endif
            {
            }
        }
        area(FactBoxes)
        {
#if A
            systempart(S1; Links)
#else
            systempart(S1; Notes)
#endif
            {
            }
        }
    }
}
