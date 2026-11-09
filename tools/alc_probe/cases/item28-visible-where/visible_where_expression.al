// Item 28: `Where` as the first operand of a property-value expression.
// expect: * accept
// source: deferred item 28, recorded by batch2/item28 2026-11-08
page 50100 "Where Probe"
{
    layout
    {
        area(Content)
        {
            field(TxtField; Txt)
            {
                Visible = Where and ShowIt;
                Enabled = Where = false;
            }
        }
    }

    var
        Txt: Text[30];
        Where: Boolean;
        ShowIt: Boolean;
}
