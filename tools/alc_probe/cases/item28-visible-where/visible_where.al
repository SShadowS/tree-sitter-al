// Item 28: `Visible = Where;` with a Boolean variable named Where.
// expect: * accept
// source: deferred item 28, recorded by batch1/probes 2026-11-08
page 50100 "Where Probe"
{
    layout
    {
        area(Content)
        {
            field(TxtField; Txt)
            {
                Visible = Where;
            }
        }
    }

    var
        Txt: Text[30];
        Where: Boolean;
}
