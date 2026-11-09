// expect: * accept
// source: deferred item 47, shape 3 in the #else arm: an empty group before the header of a preproc_split_case_extended (ERRORed on main)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
#if X
            1:
                A();
            2:
#else
#if Y
#endif
            2:
#endif
                B();
        end;
    end;

    procedure A()
    begin
    end;

    procedure B()
    begin
    end;
}
