// A group choosing a usercontrol header, the body shared after #endif; also with #elif,
// and with the group as the only header alternative inside a member-level arm.
// expect: * accept
// source: gh issue #44 repro 3; recorded 2026-11-15, alc 18.0.41
controladdin AddInA
{
    event E();
}
controladdin AddInB
{
    event E();
}
page 50100 T
{
    layout
    {
        area(Content)
        {
#if V24
            usercontrol(Logo; AddInA)
#else
            usercontrol(Logo; AddInB)
#endif
            {
                trigger E()
                begin
                end;
            }
#if V24
            usercontrol(Logo2; AddInA)
#elif V23
            usercontrol(Logo2; AddInB)
#else
            usercontrol(Logo3; AddInB)
#endif
            {
            }
        }
    }
}
