// expect: * accept
// source: review of state review C3, deferred item 108: #if/#elif/#else, every arm an if-then-begin, one shared end; ERRORs on main, C1, C3 and 3591fb69 (the #if/#else form parses)
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
        if A then begin
#endif
            Q();
        end;
        Q();
    end;

    procedure Q()
    begin
    end;
}
