codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        d: Decimal;
        b: Boolean;
        t: Text;
    begin
        b := true and true ? 1 = 1 : 2 = 2;
    end;
}
