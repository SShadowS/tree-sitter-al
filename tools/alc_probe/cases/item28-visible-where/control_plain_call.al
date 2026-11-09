// Control for visible_where_call.al: a call to a plainly named procedure as the Visible value.
// alc rejects it the same way (AL0322, semantic), so `Visible = Where();` is no syntax question.
// expect: * reject(AL0322)
// source: deferred item 28 control, recorded by batch2/item28 2026-11-08
page 50100 "Where Probe"
{
    layout
    {
        area(Content)
        {
            field(TxtField; Txt)
            {
                Visible = ShowIt();
            }
        }
    }

    var
        Txt: Text[30];

    local procedure ShowIt(): Boolean
    begin
        exit(true);
    end;
}
