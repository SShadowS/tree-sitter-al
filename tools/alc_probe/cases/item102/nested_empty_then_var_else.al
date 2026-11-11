// expect: * accept
// source: item 102 review fix 1 (an if arm holding only a nested empty group, a var else arm: clean on dcec0b4f, ERROR on 6bf7ba5d..3591fb69)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
#if B
#endif
#else
    var
        V: Integer;
#endif
    begin
    end;

    procedure P()
#if A
#if B
#endif
#else
    var
        V: Integer;
#endif
    begin
    end;

    procedure Q(): Integer
#if A
#if B
#endif
#else
    var
        V: Integer;
#endif
    begin
        exit(1);
    end;
}
