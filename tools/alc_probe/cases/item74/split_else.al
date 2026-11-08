// Fixture item_74_split_else_gap_test.txt#GAP (deferred item 74): an `else` after a `;` that only one arm supplies#0
// expect: !X accept
// expect: X reject(AL0110)
// source: deferred item 74 GAP witness, 2026-11-08; same shape as tools/alc_probe/cases/b7b3/calls/bar-group-else-semi.al
codeunit 50100 C
{
    procedure P(C: Boolean)
    begin
        if C then
            Bar()
#if X
        ;
#endif
        else
            Baz();
    end;

    procedure Bar()
    begin
    end;

    procedure Baz()
    begin
    end;
}
