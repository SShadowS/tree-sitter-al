// NOT COVERED by the F2 design (deferred item 111): a nested `#if` choosing the part header inside an arm of the
// header group. alc accepts all four configurations; the parser ERRORs (an arm holds one header, not a group).
// expect: * accept
// source: reviewer probe rv44small/probe_f2/nested_if.al; recorded 2026-11-15, alc 18.0.41
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }
}
page 50101 SubA
{
    PageType = ListPart;
    SourceTable = T;
}
page 50102 SubB
{
    PageType = ListPart;
    SourceTable = T;
}
page 50103 SubC
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
#if B
            part(P; SubA)
#else
            part(P; SubB)
#endif
#else
            part(P; SubC)
#endif
            {
            }
        }
    }
}
