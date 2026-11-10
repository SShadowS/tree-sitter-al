// expect: * accept
// source: deferred item 77 review, an attribute inside the outer arm before the nested header group
codeunit 50100 P
{
#if X
    [NonDebuggable]
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
