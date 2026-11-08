// expect: * accept
// source: issue #31 repro (31_0), hand-written in the issue
codeunit 50100 "Repro R"
{
    procedure E(X: Integer)
#if A
    var K: Integer;
#endif
#if not A
    var N: Integer;
#endif
    begin
        Glob := X + 1;
    end;

    var
        Glob: Integer;
}
