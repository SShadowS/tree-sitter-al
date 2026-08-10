codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        d: Decimal;
        b: Boolean;
        t: Text;
    begin
        i := 1 div (false ? 0 : 1);
    end;
}
