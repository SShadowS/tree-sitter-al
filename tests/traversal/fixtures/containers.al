// Non-ASCII before every group: Ærø, 😀. JS offsets are UTF-16; visits are UTF-8 bytes.
#if CLEAN25
codeunit 50100 "Containers Æ"
{
}
#else
codeunit 50100 "Containers Ø"
{
#if CLEAN24
    procedure A()
    begin
        Message('å');
    end;
#elif CLEAN23
    procedure B()
    begin
    end;
#else
    procedure C()
    begin
    end;
#endif

    procedure Stmts()
    var
        X: Integer;
    begin
        Message('control');
#if CLEAN24
        DoThing(X);
        X := 1;
#if CLEAN26
        X := 3;
#endif
#elif CLEAN23
        X := 4;
#else
        X := 2;
#endif
    end;
}
#endif
