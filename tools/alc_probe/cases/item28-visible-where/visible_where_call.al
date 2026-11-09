// Item 28: `Visible = Where();`, a call to a procedure named Where at value start: the one
// value-start form the fix leaves an ERROR (a `where(` at value start is the where_clause).
// alc rejects it with AL0322 (call not valid for client expressions), a semantic rejection the
// plain-name control `Visible = ShowIt();` gets too (control_plain_call.al).
// expect: * reject(AL0322)
// source: deferred item 28, recorded by batch2/item28 2026-11-08
page 50100 "Where Probe"
{
    layout
    {
        area(Content)
        {
            field(TxtField; Txt)
            {
                Visible = Where();
            }
        }
    }

    var
        Txt: Text[30];

    local procedure Where(): Boolean
    begin
        exit(true);
    end;
}
