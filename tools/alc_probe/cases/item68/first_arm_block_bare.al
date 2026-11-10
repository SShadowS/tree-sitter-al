// expect: * accept
// source: deferred item 68, statements before a bare `end` in the first arm, the `;` after #endif (item 69 placement)
codeunit 50000 "Item68 E"
{
    procedure P(R: Boolean)
    begin
        if R then begin
            B();
#if A
            C();
        end
#else
        end
#endif
        ;
        W();
    end;

    local procedure B()
    begin
    end;

    local procedure C()
    begin
    end;

    local procedure W()
    begin
    end;
}
