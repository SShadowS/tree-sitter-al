codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        d: Decimal;
        b: Boolean;
        t: Text;
    begin
        i := true ? 'a' : 'b';
    end;
}
