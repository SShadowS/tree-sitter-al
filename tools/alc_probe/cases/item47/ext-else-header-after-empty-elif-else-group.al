// expect: * accept
// source: deferred item 47 fix round: an empty #elif-#else group first in the #else arm, before the header of a preproc_split_case_extended
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
#elif Z
#else
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
