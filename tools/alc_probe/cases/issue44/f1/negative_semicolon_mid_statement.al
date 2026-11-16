// A `;` in the arms of a closing group where the call does not end its statement. Invalid in every
// configuration; the parser ERRORs (the arms' `;` is taken only where the call ends its statement).
// Fixture issue44_f1_gap_test.txt#Issue 44 F1 negative: a semicolon in the arms of a call inside an if condition#0
// expect: * reject(AL0104)
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1)
codeunit 50100 T
{
    procedure P1()
    begin
        if F1(1
#if A
            );
#else
            );
#endif
        then
            V(1, 1);
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure F1(I: Integer): Boolean
    begin
    end;
}
