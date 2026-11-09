// expect: * accept
// source: deferred item 47, an empty #if/#else group then a group of whole branches (ERRORed on main)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
            1:
                A();
#if X
#else
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
