// Control for item 28: the same page with an ordinary Boolean variable as the Visible value.
// expect: * accept
// source: deferred item 28 control, recorded by batch1/probes 2026-11-08
page 50100 "Where Probe"
{
    layout
    {
        area(Content)
        {
            field(TxtField; Txt)
            {
                Visible = ShowIt;
            }
        }
    }

    var
        Txt: Text[30];
        ShowIt: Boolean;
}
