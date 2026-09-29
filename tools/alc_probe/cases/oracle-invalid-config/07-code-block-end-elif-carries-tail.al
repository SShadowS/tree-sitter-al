// Fixture preproc_split_code_block_end_elif_test.txt#split code block end: %23elif branch carries the end/else-begin tail#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !A !B reject(AL0104)
// expect: !A B accept
// expect: A !B accept
// expect: A B accept
codeunit 50001 T
{
    procedure X()
    var
        x: Integer;
    begin
        if x = 1 then begin
            x := 9;
#if A
        end;
#elif B
        x := 2;
        end else begin x := 3; end;
#endif
    end;
}