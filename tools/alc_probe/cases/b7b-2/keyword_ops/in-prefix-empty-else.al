// Item 66 follow-up: a typed `in` prefix whose #else arm is empty, `B := Ok in #if X [true] in #else #endif [false];` (each directive on its own line). alc accepts both configurations (X=1 `Ok in [true] in [false]`, X=0 `Ok in [false]`); the parser ERRORs (docs/deferred-work.md item 66, not covered; test/corpus/b7b2_scope_gap_test.txt)
// expect: * accept
// source: item 66 review follow-up, 2026-10-25, alc 18.0.41 four-way probe
interface IFoo { }
interface IBar { }
codeunit 50103 Impl implements IFoo, IBar { }
codeunit 50101 P
{
    procedure Q()
    var
        B: Boolean; Ok: Boolean; F: Interface IFoo; V: Variant;
    begin
        B := Ok in
#if X
        [true] in
#else
#endif
        [false];
    end;
}
