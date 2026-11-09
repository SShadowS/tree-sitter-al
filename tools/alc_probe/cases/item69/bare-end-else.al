// expect: * accept
// source: deferred item 69, a bare `end` (no `;`) in both arms of a split block, the `;` after #endif
codeunit 50100 Demo
{
    procedure Run(R: Boolean)
    begin
        if R then begin
            A();
#if X
        end
#else
        end
#endif
        ;
        B();
    end;

    local procedure A()
    begin
    end;

    local procedure B()
    begin
    end;
}
