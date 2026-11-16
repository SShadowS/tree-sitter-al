// NOT COVERED by the F2 design (measured +53 states for the five containers, generate only):
// the same header split for an area, a group, a label, a grid, a fixed, a cuegroup, a repeater.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F2)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }
}
page 50100 P
{
    SourceTable = T;
    layout
    {
#if A
        area(Content)
#else
        area(content)
#endif
        {
#if A
            group(G1)
#else
            group(G2)
#endif
            {
#if A
                label(L1)
#else
                label(L2)
#endif
                {
                }
            }
#if A
            grid(Gr1)
#else
            grid(Gr2)
#endif
            {
            }
#if A
            fixed(F1)
#else
            fixed(F2)
#endif
            {
            }
#if A
            cuegroup(C1)
#else
            cuegroup(C2)
#endif
            {
            }
#if A
            repeater(R1)
#else
            repeater(R2)
#endif
            {
                field(K; Rec.K) { }
            }
        }
    }
}
