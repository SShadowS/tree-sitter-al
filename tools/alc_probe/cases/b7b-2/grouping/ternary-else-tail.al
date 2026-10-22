// B7b-2 Phase 0 grouping witness (spec 4.3, 5.2): `Ok ? 1 : 2 #if X + 3 #endif` = `Ok ? 1 : (2+3)`, not `(Ok ? 1 : 2)+3`.
// Typed with Dates: `Ok ? 1 : (D - D2)` compiles, `(Ok ? 1 : D) - D2` is AL0122 (ternary-else-tail__wrong.al); X=0 `Ok ? 1 : D` is AL0122.
// expect: X accept
// expect: !X reject(AL0122)
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
        I := Ok ? 1 : D
#if X
        - D2
#endif
        ;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
