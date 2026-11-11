// expect: * accept
// source: state review C3 incremental mismatch: control, the same call quoted
codeunit 50101 Probe
{
    procedure "Until"() begin end;
    procedure Main()
    begin
        "Until"();
    end;
}
