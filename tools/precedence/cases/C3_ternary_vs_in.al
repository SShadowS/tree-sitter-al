codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
        iarr: array[10] of Integer;
        barr: array[10] of Boolean;
    begin
        i := 1 in [1] ? 1 : 2;
    end;
}
