interface IProbeA
{
}

interface IProbeB
{
}

codeunit 50100 Probe
{
    procedure P(x: Interface IProbeA)
    var
        b: Boolean;
        i: Integer;
        y: Interface IProbeB;
    begin
        y := x as IProbeB;
    end;
}
