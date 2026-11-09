// expect: * accept
// source: deferred item 50, a directive-only group between a split case's end branch and the case's `end`
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
#if X
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
