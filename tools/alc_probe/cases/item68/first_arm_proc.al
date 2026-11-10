// expect: * accept
// source: deferred item 68, the issue #42 shape mirrored: statements before `end;` in the FIRST arm, procedure body
codeunit 50000 "Item68 A"
{
    procedure P()
    begin
        B();
#if A
        C();
    end;
#else
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
