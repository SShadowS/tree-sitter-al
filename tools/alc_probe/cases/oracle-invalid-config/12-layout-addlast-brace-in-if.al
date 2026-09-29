// Fixture preproc_split_layout_closing.txt#Layout addlast modification with closing brace inside %23if (no %23else)#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN28 accept
// expect: CLEAN28 reject(AL0104)
pageextension 50100 "My Extension" extends "My Page"
{
    layout
    {
        addlast(General)
        {
#if not CLEAN28
            field(MyField; Rec.MyField)
            {
                Caption = 'My Field';
            }
        }
#endif
    }
}
page 50102 "My Page"
{
    SourceTable = T2;
    layout { area(Content) { group(General) { } } }
}
table 50101 T2 { fields { field(1; AnotherField; Integer) { } field(2; MyField; Integer) { } } }
