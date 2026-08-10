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
        i := true ? 1 : 2 + 3;
    end;
}
