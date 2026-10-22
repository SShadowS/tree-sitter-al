// B7b-2 final review (Minor 4): a tail followed by a postfix, `T2 := T1 #if X + T2 #endif .ToUpper();`: X=1 `T1 + T2.ToUpper()`, X=0 `T1.ToUpper()`. The parser ERRORs at the `.` (docs/deferred-work.md item 57, receiver crossing)
// expect: * accept
// source: B7b-2 final whole-branch review fix round, 2026-10-21, alc 18.0.41 four-way probe
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
        T2 := T1
#if X
        + T2
#endif
        .ToUpper();
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
