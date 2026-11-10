// expect: * accept
// source: deferred item 68, statements before `end;` in BOTH arms, procedure body
codeunit 50000 "Item68 B"
{
    procedure P()
    begin
        B();
#if A
        C();
    end;
#else
        W();
    end;
#endif

    procedure Q()
    begin
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
