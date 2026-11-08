// expect: * accept
// source: issue #35, an unnamed return split by #if
codeunit 50100 "Repro"
{
    procedure Pick(X: Integer)
#if CLEAN27
    : Text
#else
    : Integer
#endif
    begin
        Glob := X;
    end;

    var
        Glob: Integer;
}
