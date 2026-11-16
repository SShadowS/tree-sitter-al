// A case branch whose leading patterns are chosen by #if and whose body is an every-arm-`;` call. Parses clean as
// a `case_branch` with a leading `preproc_conditional_case_patterns` (right in every configuration), while the same
// branch with a plain body is a `preproc_split_case_branch`: two shapes for one construct, deferred item 114.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 F1 re-review, finding 3)
codeunit 50100 T
{
    procedure P(X: Integer)
    begin
        case X of
#if Y
            1,
#endif
            2:
                V(1,
#if A
                  1.0);
#else
                  2.0);
#endif
            3:
                V(1, 3.0);
        end;
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
