codeunit 50113 "Directive Comments"
{
#if A // c-if
    procedure A()
    begin
    end;
#elif B // c-elif
    procedure B()
    begin
    end;
#else // c-else
    procedure C()
    begin
    end;
#endif // c-endif

    procedure Stmts()
    var
        X: Integer;
    begin
#if A // s-if
        X := 1;
#else // s-else
        X := 2;
#endif
    end;
}
