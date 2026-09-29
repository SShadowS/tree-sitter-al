// Fixture preproc_begin_end_named_test.txt#PRIORITY GUARD: begin immediately before %23endif stays preproc_split_begin#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN22 accept
// expect: CLEAN22 reject(AL0519)
codeunit 50100 T
{
    procedure E()
    var
        X: Record T2;
    begin
#if not CLEAN22
        if X.FindSet() then begin
#endif
            DoSomething();
        end;
    end;
    procedure DoSomething() begin end;
}
table 50101 T2 { fields { field(1; N; Integer) { } } }
