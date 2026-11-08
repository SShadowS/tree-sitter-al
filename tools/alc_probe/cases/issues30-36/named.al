// expect: * accept
// source: issue #35, a named return split by #if
codeunit 50100 "Repro"
{
    procedure Pick(X: Integer)
#if CLEAN27
    Result: Text
#else
    Result: Integer
#endif
    begin
        Glob := X;
    end;

    var
        Glob: Integer;
}
