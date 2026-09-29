// Fixture preproc_split_layout_closing.txt#Layout addfirst modification with closing brace inside %23if (no %23else)#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN24 accept
// expect: CLEAN24 reject(AL0104)
pageextension 50101 "My Extension2" extends "My Page"
{
    layout
    {
        addfirst(Content)
        {
#if not CLEAN24
            field(AnotherField; Rec.AnotherField)
            {
                ApplicationArea = All;
            }
        }
#endif
    }
}
page 50100 "My Page"
{
    SourceTable = T2;
    layout { area(Content) { group(General) { } } }
}
table 50101 T2 { fields { field(1; AnotherField; Integer) { } field(2; MyField; Integer) { } } }
