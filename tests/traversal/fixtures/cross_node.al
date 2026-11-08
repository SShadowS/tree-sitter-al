codeunit 50100 T
{
    procedure P()
    begin
        Message('a');
#if not C28
        Message('b');
#else
        Message(Q('c'));
    end;

    local procedure Q(T: Text): Text
    begin
        exit(T);
#endif // c-endif
    end;

    procedure R()
    begin
    end;
}
