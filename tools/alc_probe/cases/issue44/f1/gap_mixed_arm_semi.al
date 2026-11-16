// NOT COVERED by the F1 design (deferred item 110): only SOME arms of the closing group carry the statement's
// `;`, then a `;` after `#endif`. alc accepts every configuration: where the active arm has the `;` the one after
// `#endif` is an empty statement, elsewhere it is the call's terminator, so no one tree is right in every
// configuration and the parser ERRORs (as on main). P1: a call statement. P2: an assignment, the `;` in the
// other arm.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1 differential)
codeunit 50100 T
{
    procedure P1()
    begin
        Foo(1,
#if A
            3)
#else
            4);
#endif
        ;
        Bar();
    end;

    procedure P2()
    var
        D: Decimal;
    begin
        D := Foo(1, 2
#if A
            , 3);
#else
            )
#endif
        ;
        Bar();
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer; B: Integer): Decimal begin end;
    procedure Foo(A: Integer; B: Integer; C: Integer): Decimal begin end;
}
