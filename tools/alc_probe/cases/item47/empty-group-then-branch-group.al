// expect: * accept
// source: deferred item 47, an empty group then a group of whole branches after a terminated branch (ERRORed on main)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
            1:
                A();
#if X
#endif
#if Y
            3:
                C();
#endif
            2:
                B();
        end;
    end;

    procedure A()
    begin
    end;

    procedure B()
    begin
    end;

    procedure C()
    begin
    end;
}
