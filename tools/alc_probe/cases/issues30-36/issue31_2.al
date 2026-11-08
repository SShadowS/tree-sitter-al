// expect: * accept
// source: issue #31 repro (31_2), hand-written in the issue
codeunit 50100 "Repro Arm"
{
#if CLEAN27
    procedure Pick(X: Integer): Integer
#if A
    var
        K: Integer;
#endif
#if not A
    var
        N: Integer;
#endif
#else
    procedure Pick(X: Integer): Integer
    var
        M: Integer;
#endif
    begin
        exit(X + 1);
    end;
}
