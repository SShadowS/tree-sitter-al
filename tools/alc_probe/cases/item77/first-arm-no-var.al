// expect: * accept
// source: deferred item 95: a split preamble whose FIRST arm has no var section and a later arm has one
codeunit 50100 P
{
#if X
    procedure Q()
#else
    procedure Q(I: Integer)
    var
        A: Integer;
#endif
    begin
    end;
}
