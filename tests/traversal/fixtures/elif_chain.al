codeunit 50105 "Elif Chain"
{
#if CLEAN24
    procedure A()
    begin
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
#if CLEAN24
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
