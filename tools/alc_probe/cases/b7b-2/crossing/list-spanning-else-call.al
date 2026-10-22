// B7b-2 final review (Minor 4): list spanning across an #else, `Foo(1 #if X + 2 #else , 3 #endif)`: X=1 `Foo(1 + 2)`, X=0 `Foo(1, 3)` (overloads). The parser is clean and wrong (a comma-less `+2` argument), as on main (docs/deferred-work.md item 57)
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
        I := Foo(1
#if X
        + 2
#else
        , 3
#endif
        );
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
