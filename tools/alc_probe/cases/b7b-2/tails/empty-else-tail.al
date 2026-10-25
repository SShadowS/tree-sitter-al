// A tail with an empty arm (#else, #elif, or #if while a later arm is not): until, assignment,
// while, #elif, a call argument, a list element
// expect: * accept
// source: issue #38
codeunit 50101 Probe
{
    procedure P()
    var
        A: Integer;
        B: Integer;
        Ok: Boolean;
    begin
        repeat
            A := A + 1;
        until (A > 10)
#if LETHALX
            or (B > 5)
#else
#endif
        ;
        A := A
#if LETHALX
            + B
#else
#endif
        ;
        while (A < B)
#if LETHALX
            and (A > 0)
#else
#endif
        do
            A := A + 1;
        A := A
#if LETHALX
            + B
#elif OTHERY
            - B
#else
#endif
        ;
        A := A
#if LETHALX
            + B
#elif OTHERY
#else
            - B
#endif
        ;
        A := Foo(A
#if LETHALX
            + B
#else
#endif
            , B);
        A := A
#if LETHALX
#else
            + B
#endif
        ;
        A := A
#if LETHALX
#elif OTHERY
            + B
#else
            - B
#endif
        ;
        A := A
#if LETHALX
#elif OTHERY
#else
            - B
#endif
        ;
        Ok := A in [A
#if LETHALX
            + B
#else
#endif
            , B];
    end;

    procedure Foo(X: Integer; Y: Integer): Integer
    begin
        exit(X + Y);
    end;
}
