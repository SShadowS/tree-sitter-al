// B7b-2 final review (Important 1): a prefix with an empty arm, each directive on its own line: an empty #else `I := #if X a + #else #endif b;`, an empty #elif, an empty #if arm before a non-empty #else or #elif, a unary-only arm with an empty #else, a prefix after a binary operator, an all-empty group at an assignment right `I := #if X #else #endif b;` (still ERRORs: not a prefix, and not a statement there), and an action's `Visible = #if X #else not #endif Ok;` / `#if X not #else #endif` (page 50102). alc accepts every configuration; the parser ERRORed on the codeunit statements and read the two page values as a comma-less option list, until item 66's fix (docs/deferred-work.md item 66; test/corpus/b7b2_prefix_empty_arm_test.txt)
// expect: * accept
// source: B7b-2 small-correctness batch final whole-branch review, 2026-10-25 (finding I1), alc 18.0.41 four-way probe; the #elif, empty-#if-first, unary, binary-right and page shapes added by item 66's fix, 2026-10-25
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; a: Integer; b: Integer; c: Integer;
    begin
        I :=
#if X
        1 +
#else
#endif
        2;
        I :=
#if X
        a +
#elif Y
#else
        a -
#endif
        b;
        I :=
#if X
#else
        a +
#endif
        b;
        I :=
#if X
#elif Y
        a *
#else
        a -
#endif
        b;
        I :=
#if X
#elif Y
#else
        a -
#endif
        b;
        I :=
#if X
        -
#else
#endif
        b;
        I := c *
#if X
        a +
#else
#endif
        b;
        I :=
#if X
#else
#endif
        b;
    end;
}
page 50102 PG
{
    actions
    {
        area(Processing)
        {
            action(A2)
            {
                Visible =
#if X
#else
                    not
#endif
                    Ok;
                Enabled =
#if Y
                    not
#else
#endif
                    Ok;
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        Ok: Boolean;
}
