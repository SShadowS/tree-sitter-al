// Every arm carries the statement's `;`, then a `;` after `#endif`: `Foo(1, 3);;`, an empty statement after the
// call in every configuration; then a second statement. Covered: the call ends its statement inside the arms and
// the `;` after `#endif` is an empty_statement (the differential's blocker on the first F1 design read it as the
// call's terminator). P2: an assignment, three arms.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1 differential)
codeunit 50100 T
{
    procedure P1()
    begin
        Foo(1,
#if A
            3);
#else
            3);
#endif
            ;
        Bar();
    end;

    procedure P2()
    var
        D: Decimal;
    begin
        D := Foo(1
#if A
            , 3);
#elif B
            , 4);
#else
            , 5);
#endif
            ;
        Bar();
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer; B: Integer): Decimal begin end;
}
