codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
    begin
        b := 1 <> 2 xor 3 <> 4;
    end;
}
