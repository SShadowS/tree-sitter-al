// B7b-2 Task 13: an operand group at the right of `in` whose #else arm is not a list: `b := i in #if X [1, 2] #else 3 #endif;`. The parser accepts every configuration (in's right is the general operand group, spec execution amendments Task 10, typed rights); docs/deferred-work.md item 58
// Fixture b7b2_operand_group_test.txt#B7b-2 operand group: OVERACCEPT in's right takes a non-list arm (item 58)#0
// expect: !X reject(AL0104)
// expect: X accept
// source: B7b-2 Task 13, 2026-10-21, alc 18.0.41 four-way probe
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
        B := I in
#if X
        [1, 2]
#else
        3
#endif
        ;
    end;

    procedure Bar() begin end;
    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Foo(A: Integer; C: Integer): Integer begin exit(A + C); end;
}
