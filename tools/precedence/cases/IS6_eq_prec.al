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
    begin
        b := true = x is IProbeB;
    end;
}
