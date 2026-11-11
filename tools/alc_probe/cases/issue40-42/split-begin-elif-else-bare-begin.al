// expect: * accept
// source: review of state review C3, deferred item 108 (rvC3 chains2.py elifA with one block): #if/#elif/#else, two if-then-begin arms and a bare begin, one shared end; ERRORs on main, C1, C3 and 3591fb69
codeunit 50100 X
{
    procedure P(A: Boolean; G: Boolean)
    begin
        Q();
#if not C
        if A then begin
#elif D
        if G then begin
#else
        begin
#endif
            Q();
        end;
        Q();
    end;

    procedure Q()
    begin
    end;
}
