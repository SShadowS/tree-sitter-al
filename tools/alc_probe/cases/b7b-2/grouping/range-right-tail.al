// B7b-2 Phase 0 grouping witness (spec 4.3, 5.2): `[1..5 #if X + 2 #endif]` = `[1..(5+2)]`. `..` is no expression operator, so the other reading has no meaning: ladder-derived, acceptance recorded.
// expect: * accept
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
        B := I in [1..5
#if X
        + 2
#endif
        ];
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
