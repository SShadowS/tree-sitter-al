// expect: * accept
// source: deferred item 77 review, a nested group of header + var section (preproc_split_procedure_preamble's cousin)
codeunit 50100 P
{
#if X
#if Y
    procedure Q()
    var
        A: Integer;
#else
    procedure Q(I: Integer)
    var
        A: Integer;
#endif
#else
    procedure Q(J: Code[10])
    var
        A: Integer;
#endif
    begin
        A := 1;
    end;
}
