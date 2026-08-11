codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        d: Decimal;
        b: Boolean;
        t: Text;
        arr: array[10] of Integer;
    begin
        d := 1 / (0.0000000000000000001 / 0.0000000000000000001);
    end;
}
