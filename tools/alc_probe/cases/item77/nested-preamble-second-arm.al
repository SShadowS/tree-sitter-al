// expect: * accept
// source: deferred item 83: a nested preamble group in an #elif arm of a split preamble
codeunit 50100 P
{
#if X
    procedure Q()
    var
        A: Integer;
#elif Y
#if Z
    procedure Q(I: Integer)
    var
        A: Integer;
#else
    procedure Q(I: Code[10])
    var
        B: Integer;
#endif
#else
    procedure Q(J: Code[10])
    var
        A: Integer;
#endif
    begin
    end;
}
