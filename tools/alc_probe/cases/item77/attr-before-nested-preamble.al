// expect: * accept
// source: deferred item 82: an attribute inside the outer arm before a nested group of preambles (item 83's shape)
codeunit 50100 P
{
#if X
    [NonDebuggable]
#if Y
    procedure Q()
    var
        A: Integer;
#else
    procedure Q(I: Integer)
    var
        A: Integer;
#endif
#else
    procedure Q(J: Code[10])
    var
        A: Integer;
#endif
    begin
    end;
}
