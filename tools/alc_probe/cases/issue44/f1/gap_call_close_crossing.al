// NOT COVERED by the F1 design: the arm carries more than `[arguments] ) [;]`.
// P2: an exit value, two `)` in each arm. P3: an if condition, the arms carry `) > 1 then`.
// P4: a nested call, two `)` in each arm. P5: the expression continues after the `)` inside
// the arm (`) + 1;`). P6: a statement follows the `;` inside the arm. P8: an operator tail
// inside the arm before the `)` (deferred item 57's list-spanning neighbour).
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1)
codeunit 50100 T
{
    procedure P2(): Decimal
    begin
        exit(F1(
#if A
            1));
#else
            2));
#endif
    end;

    procedure P3()
    begin
        if F1(1
#if A
            ) > 1 then
#else
            ) > 2 then
#endif
            V(1, 1);
    end;

    procedure P4()
    begin
        V(1, F1(
#if A
            1));
#else
            2));
#endif
    end;

    procedure P5()
    var
        D: Decimal;
    begin
        D := F1(
#if A
            1) + 1;
#else
            2) + 2;
#endif
    end;

    procedure P6()
    begin
        V(1,
#if A
          1.0);
        V(2, 2.0);
#else
          2.0);
#endif
    end;

    procedure P8()
    begin
        V(1, 2
#if A
            + 1);
#else
            );
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure F1(I: Integer): Decimal
    begin
    end;
}
