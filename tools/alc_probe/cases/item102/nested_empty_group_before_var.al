// expect: * accept
// source: deferred item 102 (a nested empty group between a routine header and var ERRORed)
codeunit 50100 Demo
{
    procedure P(): Integer
#if X
#if Y
#endif
#endif
    var
        V: Integer;
    begin
        V := 1;
        exit(V);
    end;
}
