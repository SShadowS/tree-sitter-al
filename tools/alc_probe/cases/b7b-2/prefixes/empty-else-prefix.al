// B7b-2 final review (Important 1): a prefix whose #else is empty, `I := #if X 1 + #else #endif 2;` (each directive on its own line). alc accepts both configurations (X=1: `1 + 2`; X=0: `2`); the parser ERRORs (docs/deferred-work.md item 66; test/corpus/b7b2_scope_gap_test.txt)
// expect: * accept
// source: B7b-2 small-correctness batch final whole-branch review, 2026-10-25 (finding I1), alc 18.0.41 four-way probe
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer;
    begin
        I :=
#if X
        1 +
#else
#endif
        2;
    end;
}
