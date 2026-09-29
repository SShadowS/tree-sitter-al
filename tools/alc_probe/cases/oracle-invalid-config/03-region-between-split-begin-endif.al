// Fixture preproc_define_undef_test.txt#Scanner lookahead: %23region between a split begin and its %23endif#0
// source: fixture gained `#endregion` in A3 fix round 2 (2026-09-29, re-review m3); alc 18.0.41 re-probed then. Before, CLEAN27=0 was AL0622 (unterminated region) and CLEAN27=1 a split/flat MISMATCH
// expect: !CLEAN27 accept
// expect: CLEAN27 reject(AL0519)
codeunit 50001 T
{
    procedure X() : Boolean
    var
        Ok: Boolean;
    begin
#if not CLEAN27
        if not Ok then begin
#region Inner
#endregion
#endif
            exit(false);
        end;
    end;
}