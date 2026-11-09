// expect: !X accept
// expect: X reject(AL0111)
// source: deferred item 69, a bare `end` in the #if arm, `end;` in the #else arm, no `;` after #endif (X: `end B();` lacks its separator, AL0111)
codeunit 50100 Demo
{
    procedure Run(R: Boolean)
    begin
        if R then begin
            A();
#if X
        end
#else
        end;
#endif
        B();
    end;

    local procedure A()
    begin
    end;

    local procedure B()
    begin
    end;
}
