// expect: * accept
// source: item 102 review fix 1 (a var group, an empty group, a var group before begin; the second var group is `not A` because two var sections are AL0104: clean on dcec0b4f, ERROR on 6bf7ba5d..3591fb69)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
    var
        V: Integer;
#endif
#if B
#endif
#if not A
    var
        W: Integer;
#endif
    begin
    end;

    procedure P()
#if A
    var
        V: Integer;
#endif
#if B
#endif
#if not A
    var
        W: Integer;
#endif
    begin
    end;

    procedure Q(): Integer
#if A
    var
        V: Integer;
#endif
#if B
#endif
#if not A
    var
        W: Integer;
#endif
    begin
        exit(1);
    end;
}
