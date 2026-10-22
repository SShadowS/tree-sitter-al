// B7b-2 Phase 0 grouping witness (spec 4.3): `a * b #if X + c #endif` = `(a*b)+c`, not `a*(b+c)`.
// AL0370 instrument: `1 div ((0*1)+1)` folds to 1 div 1, `1 div (0*(1+1))` to 1 div 0 (mul-tail__wrong.al).
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
        I := 1 div (0 * 1
#if X
        + 1
#endif
        );
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
