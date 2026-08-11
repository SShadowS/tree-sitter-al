interface IProbe
{
}

codeunit 50101 ProbeImpl implements IProbe
{
}

codeunit 50100 Probe
{
    procedure P(x: Interface IProbe)
    begin
        if x is ProbeImpl then
            exit;
    end;
}
