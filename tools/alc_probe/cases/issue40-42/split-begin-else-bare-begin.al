// expect: * accept
// source: review of state review C3, deferred item 108: #if/#else, one arm an if-then-begin, the other a bare begin, one shared end; ERRORs on main, C1, C3 and 3591fb69
codeunit 50100 X
{
    procedure P(A: Boolean; G: Boolean)
    begin
        Q();
#if not C
        if A then begin
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
