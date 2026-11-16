// NOT COVERED by the F2 design (deferred item 111): the arms choose between a page `field(...)` and a `part(...)`
// header over one shared body. alc accepts both configurations; the parser ERRORs (preproc_split_part arms are
// part-like headers only, preproc_split_field arms field headers only).
// expect: * accept
// source: reviewer probe rv44small/probe_f2/field_vs_part.al; recorded 2026-11-15, alc 18.0.41
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }
}
page 50102 SubB
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
            field(P; Rec.K)
#else
            part(P; SubB)
#endif
            {
            }
        }
    }
}
