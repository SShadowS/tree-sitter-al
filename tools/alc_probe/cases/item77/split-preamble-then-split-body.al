// expect: * accept
// source: deferred item 96 (from item 82's review, batch 6): a split preamble (header + var section in each arm) followed by a split body
codeunit 50100 P
{
#if X
    procedure Q()
    var
        A: Integer;
#else
    procedure Q(I: Integer)
    var
        A: Integer;
#endif
#if Z
    begin
        A := 1;
#else
    begin
        A := 2;
#endif
    end;
}
