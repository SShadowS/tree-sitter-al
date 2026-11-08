// expect: * accept
// source: issue #32 repro (32_0), hand-written in the issue
codeunit 50100 "Repro P"
{
#if CLEAN27
    trigger OnRun()
    var
        K: Integer;
#else
    trigger OnRun()
    var
        M: Integer;
#endif
    begin
        Glob := Glob + 2;
    end;

    var
        Glob: Integer;
}
