// expect: * accept
// source: deferred item 67, an empty group before a then-branch
codeunit 50100 Demo
{
    procedure Run(R: Boolean; I: Integer)
    begin
        if R then
#if F
#endif
            A()
        else
            B();
    end;

    local procedure A()
    begin
    end;

    local procedure B()
    begin
    end;
}
