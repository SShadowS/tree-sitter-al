// Fixture preproc_split_block_over_endif_test.txt#A block opened inside a %23if branch that also contributes statements#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN27 accept
// expect: CLEAN27 reject(AL0519)
codeunit 50000 T
{
    procedure P()
    begin
#if not CLEAN27
        if true then begin
            Message('a');
#endif
            Message('b');
        end;
    end;
}
