// Fixture preproc_split_operator_negative_test.txt#DELIBERATE NEGATIVE -- the OPERATOR itself on the far side of a %23if boundary#0
// X=1 is VALID AL (split and flat), and tree-sitter-al ERRORs on it: a grammar gap owned by roadmap B3 (docs/deferred-work.md item 3). Only X=0 is a negative.
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !X reject(AL0104,AL0111)
// expect: X accept
codeunit 50203 D { procedure P() var i: Integer; begin i := 1
#if X
 +
#endif
 2; end; }
