// expect: * accept
// source: deferred item 77, #elif in both the outer and the nested header group, a return type and a body var section
codeunit 50100 P
{
#if X
#if Y
    procedure Q(): Integer
#elif Z
    local procedure Q(I: Integer): Integer
#else
    procedure Q(L: Text): Integer
#endif
#elif Y
    procedure Q(J: Code[10]): Integer
#else
    procedure Q(K: Boolean): Integer
#endif
    var
        V: Integer;
    begin
        exit(V);
    end;
}
