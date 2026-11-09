// expect: * accept
// source: deferred item 47 fix round: an empty #elif group before the #if arm's header of a preproc_split_case_extended, after a branch (reviewer's minimal; main parsed it as a sibling group)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
#if X
            1:
                A();
#if Y
#elif Z
#endif
            2:
#else
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
