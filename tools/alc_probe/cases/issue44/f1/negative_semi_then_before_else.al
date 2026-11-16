// Every arm of the closing group carries the `;` and the call is an if's then-branch followed by `else`:
// `if C then V(1, 1.0); else ...` in every configuration, a `;` before `else`. Invalid in every configuration;
// the parser ERRORs (an every-arm-`;` then-branch takes no else).
// Fixture issue44_f1_gap_test.txt#Issue 44 F1 negative: every arm carries the semicolon in a then-branch followed by else#0
// expect: * reject(AL0110)
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 F1 review, bodies)
codeunit 50100 T
{
    procedure Q1(C: Boolean)
    begin
        if C then
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        else
            V(1, 3.0);
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
