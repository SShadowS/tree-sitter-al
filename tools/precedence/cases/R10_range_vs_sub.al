codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
    begin
        b := 1 in [4 - 2 .. 4];
    end;
}
