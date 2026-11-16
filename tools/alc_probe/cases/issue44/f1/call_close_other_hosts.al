// The closing group where the call is not a whole call statement, or the `;` is elsewhere.
// P1: the call is an assignment's right. P7: the last statement of a block, no `;` anywhere.
// P9: the statement sits inside an arm of an outer statement group.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1)
codeunit 50100 T
{
    procedure P1(): Decimal
    var
        D: Decimal;
    begin
        D := F1(
#if A
            1);
#else
            2);
#endif
        exit(D);
    end;

    procedure P7()
    begin
        V(1,
#if A
          1.0)
#else
          2.0)
#endif
    end;

    procedure P9()
    begin
#if B
        V(1,
#if A
          1.0);
#else
          2.0);
#endif
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure F1(I: Integer): Decimal
    begin
    end;
}
