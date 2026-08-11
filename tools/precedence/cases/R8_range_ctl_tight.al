codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
    begin
        b := 1 in [1 + (1 .. 4)];
    end;
}
