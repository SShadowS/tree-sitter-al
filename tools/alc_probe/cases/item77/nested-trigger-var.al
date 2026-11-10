// expect: * accept
// source: deferred item 85: a nested trigger preamble group, a var section in some arms only
codeunit 50100 P
{
#if X
#if Y
    trigger OnRun()
    var
        A: Integer;
#else
    trigger OnRun()
#endif
#else
    trigger OnRun()
    var
        A: Integer;
#endif
    begin
    end;
}
