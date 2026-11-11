// expect: * accept
// source: deferred item 102 (a nested empty group between a routine header and begin was a var-less var block)
codeunit 50100 Demo
{
    procedure P(): Integer
#if X
#if Y
#endif
#endif
    begin
        exit(1);
    end;
}
