codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
    begin
        i := true and true ? 1 : 2;
    end;
}
