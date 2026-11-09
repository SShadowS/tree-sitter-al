// expect: * accept
// source: deferred item 69, the closing region of a block opened in an earlier region holds a group of bare `end`s (B7a occ:_preproc_end_guard:3.0)
codeunit 50100 Demo
{
    procedure Run(R: Boolean)
    begin
#if T
        if R then A() else begin
#else
        if not R then A() else
#endif
        B();
#if T
#if X
        end
#else
        end
#endif
        ;
#endif
        A();
    end;

    local procedure A()
    begin
    end;

    local procedure B()
    begin
    end;
}
