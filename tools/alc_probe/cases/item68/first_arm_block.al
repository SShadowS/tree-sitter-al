// expect: * accept
// source: deferred item 68, statements before `end;` in the first arm, a nested code_block (if R then begin)
codeunit 50000 "Item68 D"
{
    procedure P(R: Boolean)
    begin
        if R then begin
            B();
#if A
            C();
        end;
#else
        end;
#endif
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
