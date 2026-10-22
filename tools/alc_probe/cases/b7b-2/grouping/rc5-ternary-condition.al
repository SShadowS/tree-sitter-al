// B7b-2 Phase 0 grouping witness (spec 4.3, 5.2, RC5): `Ok or true #if X and false #endif or Ok ? 1 : 2` = `((Ok or (true and false)) or Ok) ? 1 : 2`.
// The RC5 reading `... or (Ok ? 1 : 2)` is AL0175 'or' Boolean and Integer (rc5-ternary-condition__wrong.al).
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
        I := Ok or true
#if X
        and false
#endif
        or Ok ? 1 : 2;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
