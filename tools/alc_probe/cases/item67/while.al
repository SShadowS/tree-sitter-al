// expect: * accept
// source: deferred item 67, an empty group before a while body
codeunit 50100 Demo
{
    procedure Run(R: Boolean; I: Integer)
    begin
        while R do
#if F
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
