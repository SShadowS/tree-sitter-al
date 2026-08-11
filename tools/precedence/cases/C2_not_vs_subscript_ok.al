codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
        iarr: array[10] of Integer;
        barr: array[10] of Boolean;
    begin
        b := not barr[1];
    end;
}
