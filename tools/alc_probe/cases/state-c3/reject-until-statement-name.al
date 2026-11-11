// expect: * reject(AL0104,AL0111,AL0224)
// source: state review C3 incremental mismatch: `until` at a statement start is reserved (statement_names)
codeunit 50101 Probe
{
    procedure "Until"() begin end;
    procedure Main()
    begin
        Until();
    end;
}
