// B7b-2 Phase 0 grouping witness (spec 4.3): `2 * #if X 3 + 4 #else 5 #endif` = `(2*3)+4` at X, not `2*(3+4)`.
// AL0370 instrument with a 0 for the 2: `(0*3)+4` = 4, `0*(3+4)` = 0 (mul-group__wrong.al); X=0 is `0*5` = 0.
// expect: X accept
// expect: !X reject(AL0370)
// source: B7b-2 Phase 0, 2026-10-20
interface IFoo { }
interface IBar { }
codeunit 50103 Impl implements IFoo, IBar { }
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; J: Integer; B: Boolean; Ok: Boolean; Ok2: Boolean; T1: Text; T2: Text;
        F: Interface IFoo; G: Interface IBar; V: Variant; D: Date; D2: Date; CU: Codeunit P;
    begin
        I := 1 div (0 *
#if X
        3 + 4
#else
        5
#endif
        );
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
