// A source SEMANTIC error in the AL1xxx range: located in Test.al, so REJECT, not BROKEN.
// Pins the location rule of tools/alc_probe/core.classify (A2 fix round 1, review I1).
// expect: * reject(AL1073)
// source: recorded by A2, 2026-09-29 (alc 18.0.41: Test.al(7,15): error AL1073, the procedure has the same name as a declared trigger)
codeunit 50100 P
{
    trigger OnRun()
    begin
    end;

    procedure OnRun()
    begin
    end;
}
