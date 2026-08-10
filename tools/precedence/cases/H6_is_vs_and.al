interface IProbe
{
}

codeunit 50101 ProbeImpl implements IProbe
{
}

codeunit 50100 Probe
{
    procedure P(x: Interface IProbe)
    var
        b: Boolean;
    begin
        b := true and x is Codeunit ProbeImpl;
    end;
}
