// expect: * accept
// source: deferred item 102 (an empty #if/#elif/#else group between a routine header and begin was a var-less var block)
codeunit 50100 Demo
{
    procedure P(): Integer
#if X
#elif Y
#else
#endif
    begin
        exit(1);
    end;
}
