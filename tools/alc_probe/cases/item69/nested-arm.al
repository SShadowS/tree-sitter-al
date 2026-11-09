// expect: * accept
// source: deferred item 69, an arm of a split block end that is itself a group of bare `end`s (B7a occ:_preproc_end_branch:0.1.0)
codeunit 50100 Demo
{
    procedure Run(R: Boolean)
    begin
        if R then begin
            A();
#if T
#if X
        end
#else
        end
#endif
        ;
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
