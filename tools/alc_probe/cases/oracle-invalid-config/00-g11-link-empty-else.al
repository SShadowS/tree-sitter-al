// Fixture link_list_opening_conditional_test.txt#G11: whole value with an empty %23else arm is unchanged#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !X reject(AL0104,AL0219)
// expect: X accept
page 50100 P
{
    layout
    {
        area(Content)
        {
            part(L; Q)
            {
                Caption =
#if X
                    'a';
#endif
            }
        }
    }
}
page 50101 Q
{
    PageType = CardPart;
}
