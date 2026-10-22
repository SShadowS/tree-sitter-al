// B7b-2 Phase 0: `as` as a tail operator, placement `consecutive` (RC4, item 41)
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
        F := F
#if X
        as IFoo
#endif
#if Y
        as IFoo
#endif
        ;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
