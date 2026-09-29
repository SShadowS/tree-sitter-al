// Fixture preproc_define_undef_test.txt#Scanner lookahead: %23region between a split begin and its %23endif#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN27 reject(AL0622)
// expect: CLEAN27 reject(AL0104,AL0622)
// expect-mismatch: CLEAN27
codeunit 50001 T
{
    procedure X() : Boolean
    var
        Ok: Boolean;
    begin
#if not CLEAN27
        if not Ok then begin
#region Inner
#endif
            exit(false);
        end;
    end;
}