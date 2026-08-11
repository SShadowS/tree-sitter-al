codeunit 50100 Probe
{
    procedure P()
    var
        arr: array[1 + 2 * 3] of Integer;
    begin
        arr[7] := 0;
    end;
}
