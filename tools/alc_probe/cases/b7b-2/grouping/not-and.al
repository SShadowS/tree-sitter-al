// B7b-2 Phase 0 grouping witness (spec 4.3): `not a #if X and c #endif` = `(not a) and c`, not `not (a and c)`.
// a Integer, c Boolean: `(not I) and Ok` is AL0173 (unary operand), `not (I and Ok)` is AL0175 (not-and__wrong.al).
// expect: * reject(AL0173)
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
        B := not I
#if X
        and Ok
#endif
        ;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
