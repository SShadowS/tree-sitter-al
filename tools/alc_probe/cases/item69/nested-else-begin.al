// expect: * accept
// source: deferred item 69, the `else begin` block of a split block end closes with a group of bare `end`s (B7a occ:_else_begin_block:4.0)
codeunit 50100 Demo
{
    procedure Run(R: Boolean)
    begin
        if R then begin
            A();
#if T
        end else begin
            B();
#if X
        end
#else
        end
#endif
        ;
#else
        end;
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
