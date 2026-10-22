// B7b-2 Phase 0: receiver crossing (spec 3.4), `#if X 1 + T1 #else T1 #endif .IndexOf('a')`.
// X=1 types only as `1 + (T1.IndexOf('a'))`; `(1 + T1).IndexOf` is AL0175 (grouping/receiver__wrong.al).
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
        I :=
#if X
        1 + T1
#else
        T1
#endif
        .IndexOf('a');
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
