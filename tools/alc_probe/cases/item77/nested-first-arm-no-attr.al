// expect: * accept
// source: deferred item 77, a nested #if choosing the header in the first arm, no attribute
codeunit 50100 P
{
#if X
#if Y
    procedure Q()
#else
    procedure Q(I: Integer)
#endif
#else
    procedure Q(J: Code[10])
#endif
    begin
    end;
}
