// expect: * accept
// source: issue #30 repro (30_0), hand-written in the issue
codeunit 50100 "Nested Var Demo"
{
    procedure Pick(X: Integer): Integer
    var
        A: Integer;
#if not ALPHA
        B: Integer;
#if BETA
        C: Integer;
#endif
#endif
    begin
        exit(X);
    end;
}
