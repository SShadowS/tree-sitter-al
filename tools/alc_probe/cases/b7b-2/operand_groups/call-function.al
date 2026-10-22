// B7b-2 Task 10 fix round 1 (review M4): a receiver group as the callee, `#if X Foo #else Baz #endif (1)` (spec 3.4), in an expression and as a statement
// expect: * accept
// source: B7b-2 Task 10 fix round 1, 2026-10-21
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer;
    begin
        I :=
#if X
        Foo
#else
        Baz
#endif
        (1);
#if X
        Foo
#else
        Baz
#endif
        (2);
    end;

    procedure Foo(A: Integer): Integer begin exit(A); end;
    procedure Baz(A: Integer): Integer begin exit(A + 1); end;
}
