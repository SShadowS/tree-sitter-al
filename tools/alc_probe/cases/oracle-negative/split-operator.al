// Fixture preproc_split_operator_test.txt#An OPERATOR alone in a %23if arm: the operand follows %23endif#0
// X=1 is VALID AL (split and flat), parsed since B3 (2026-10-01) by preproc_conditional_expression_tail's operator-only form. Only X=0 is a negative.
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !X reject(AL0104,AL0111)
// expect: X accept
codeunit 50203 D { procedure P() var i: Integer; begin i := 1
#if X
 +
#endif
 2; end; }
