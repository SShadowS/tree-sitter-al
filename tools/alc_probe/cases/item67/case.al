// expect: * accept
// source: deferred item 67, an empty group before a case-branch body
codeunit 50100 Demo
{
    procedure Run(R: Boolean; I: Integer)
    begin
        case I of
            1:
#if F
#endif
                A();
        end;
    end;

    local procedure A()
    begin
    end;

    local procedure B()
    begin
    end;
}
