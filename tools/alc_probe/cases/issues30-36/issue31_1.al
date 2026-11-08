// expect: * accept
// source: issue #31 repro (31_1), hand-written in the issue
codeunit 50100 "Repro R"
{
    procedure E(X: Integer)
#if A
#if B
    var K: Integer;
#endif
#endif
    begin
        Glob := X + 1;
    end;

    var
        Glob: Integer;
}
