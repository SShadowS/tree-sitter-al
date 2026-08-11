codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        d: Decimal;
        b: Boolean;
        t: Text;
    begin
        d := 1 / 0.00000000000000000001 / 0.00000000000000000001;
    end;
}
