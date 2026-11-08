// expect: * accept
// source: deferred item 67, an empty group before an else-branch
codeunit 50100 Demo
{
    procedure Run(R: Boolean; I: Integer)
    begin
        if R then
            A()
        else
#if F
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
