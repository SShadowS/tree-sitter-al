// B7b-2 Phase 0 grouping witness (spec 4.3): `true and #if X a = c #else d #endif` = `(true and a) = c`, not `true and (a = c)`.
// a, c Integer: `(true and I) = J` is AL0175, `true and (I = J)` compiles (and-eq-group__wrong.al).
// expect: X reject(AL0175)
// expect: !X accept
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
        B := true and
#if X
        I = J
#else
        Ok
#endif
        ;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
