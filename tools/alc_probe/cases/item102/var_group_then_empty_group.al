// expect: * accept
// source: item 102 review fix 1 (a var group then an empty group before begin: clean on dcec0b4f, ERROR on 6bf7ba5d..3591fb69)
codeunit 50100 Demo
{
    trigger OnRun()
#if A
    var
        V: Integer;
#endif
#if B
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
    begin
    end;

    procedure Q(): Integer
#if A
    var
        V: Integer;
#endif
#if B
#endif
    begin
        exit(1);
    end;
}
