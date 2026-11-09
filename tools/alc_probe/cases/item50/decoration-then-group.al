// expect: * accept
// source: deferred item 50, a decoration before the end branch's own `;`, then a group of branches before the case's `end`
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
            1:
                A();
            2:
#if TPL
                A()
#if D
#endif
                ;
#if X
            3:
                A();
#endif
        end;
        I := 1;
#else
                A();
        end;
        I := 2;
#endif
    end;

    procedure A()
    begin
    end;
}
