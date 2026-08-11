codeunit 50100 Probe
{
    procedure P()
    var
        i: Integer;
        b: Boolean;
    begin
        case i of
            1 + (1 .. 4):
                ;
        end;
    end;
}
