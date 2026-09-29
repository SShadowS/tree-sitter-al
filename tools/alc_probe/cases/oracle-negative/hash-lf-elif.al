// Fixture preproc_if_elif_whitespace_tolerance_test.txt#NEGATIVE: `%23` then a bare LF then `elif` on the next line must NOT be#0
// alc reads the lone `#` as an unknown directive (AL0621) in every configuration; our resolver does not see a directive there, so the flat text of !CLEAN24 compiles: the expected mismatch.
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN24 reject(AL0621)
// expect-mismatch: !CLEAN24
// expect: CLEAN24 reject(AL0104,AL0198,AL0621)
codeunit 50000 "If Test"
{
    #if CLEAN24
    procedure Test()
    begin
    end;
    #
elif CLEAN23
    procedure Test2()
    begin
    end;
    #endif
}
