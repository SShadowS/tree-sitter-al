// expect: * accept
// source: item 102 review fix 1 (a var if arm, an else arm holding only a nested empty group: clean on dcec0b4f, ERROR on 6bf7ba5d..3591fb69)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
    var
        V: Integer;
#else
#if B
#endif
#endif
    begin
    end;

    procedure P()
#if A
    var
        V: Integer;
#else
#if B
#endif
#endif
    begin
    end;

    procedure Q(): Integer
#if A
    var
        V: Integer;
#else
#if B
#endif
#endif
    begin
        exit(1);
    end;
}
