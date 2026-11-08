// expect: * accept
// source: issue #35, only the return type split by #if
codeunit 50100 "Repro"
{
    procedure Pick(X: Integer) Result:
#if CLEAN27
    Text
#else
    Integer
#endif
    begin
        Glob := X;
    end;

    var
        Glob: Integer;
}
