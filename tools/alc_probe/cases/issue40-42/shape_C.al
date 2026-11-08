// expect: * accept
// source: issue #42 shape C (invented), procedures declared
codeunit 50000 "Shape C"
{
    procedure P()
    begin
        B();
#if A
    end;
#else
        C();
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
