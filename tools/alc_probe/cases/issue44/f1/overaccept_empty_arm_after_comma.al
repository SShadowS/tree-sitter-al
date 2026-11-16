// OVER-ACCEPTED by the F1 design (deferred item 44): an arm with no argument after a `,` (`V(1, )` in that
// configuration). The leading arm shape takes an optional run, which the group needs at the list's start
// (`Foo( #if A 1) #else ) #endif`, `Foo()`); after a `,` it is never valid. The parser reads it clean.
// expect: * accept
// expect: A reject(AL0301)
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1 differential)
codeunit 50100 T
{
    procedure P1()
    begin
        V(1,
#if A
          );
#else
          2);
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
