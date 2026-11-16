// The part header split for a `chartpart`: the header differs per arm, the body is shared after `#endif`
// (preproc_split_part; fixture issue44_f2_split_part_test.txt "chartpart header split").
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 F2 review: the chartpart claim had no probe)
page 50100 P
{
    layout
    {
        area(Content)
        {
#if A
            chartpart(C; Q1)
#else
            chartpart(C; Q2)
#endif
            {
            }
        }
    }
}
