// A group whose arms carry the END of a call statement and its `;`.
// P1: the issue's repro 1 (an argument, `)`, `;`). P2: repro 2 (`, arg);` against `);`).
// P3: a member callee. P4: three arms. P5: the `)` in the arms and the `;` shared.
// P6: a comment and a pragma inside the arms. P7: the group is the whole argument list.
// expect: * accept
// source: gh issue #44 repros 1 and 2; recorded 2026-11-15, alc 18.0.41
codeunit 50100 T
{
    procedure P1()
    begin
        V(
          1,
#if A
          F1(1));
#else
          F2(1));
#endif
    end;

    procedure P2()
    begin
        Foo(1, 2
#if A
            , true);
#else
            );
#endif
    end;

    procedure P3()
    var
        C: Codeunit T;
    begin
        C.V(1,
#if A
            C.F1(1));
#else
            C.F2(1));
#endif
        C.P1();
    end;

    procedure P4()
    begin
        V(1,
#if A
          F1(1));
#elif B
          F2(1));
#else
          F1(2));
#endif
    end;

    procedure P5()
    begin
        V(1,
#if A
          F1(1))
#else
          F2(1))
#endif
        ;
    end;

    procedure P6()
    begin
        V(1,
#if A
          // old
          F1(1)); // done
#else
#pragma warning disable AA0137
          F2(1));
#pragma warning restore AA0137
#endif
    end;

    procedure P7()
    begin
        Foo(
#if A
            1, 2, true);
#else
            1, 2);
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure F1(I: Integer): Decimal
    begin
    end;

    procedure F2(I: Integer): Decimal
    begin
    end;

    procedure Foo(A: Integer; B: Integer)
    begin
    end;

    procedure Foo(A: Integer; B: Integer; C: Boolean)
    begin
    end;
}
