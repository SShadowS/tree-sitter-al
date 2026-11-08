// Negative control for item 28: with no variable named Where, alc resolves `Where` as a name and fails,
// so the accepting case really reads the variable (the word is not skipped as a keyword).
// expect: * reject(AL0118,AL0208)
// source: deferred item 28 negative control, recorded by batch1/probes 2026-11-08
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
}
