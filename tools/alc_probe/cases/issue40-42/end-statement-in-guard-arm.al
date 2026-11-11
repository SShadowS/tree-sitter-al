// `End;` as a statement inside the arm of a guarded statement: alc reserves `end` at a statement start
// (AL0519 family), so X=1 is rejected; X=0 is the plain `A := 1;`. main parsed X=1 clean as a call named
// End; since state review C3 it is an ERROR (tools/config_oracle/tests/test_end_name_positions.py, row
// guard_arm_end_statement).
// expect: * accept
// expect: X reject(AL0104,AL0198)
// source: state review C3 review F2 (scratchpad rvC3/alc/guard_end.al)
codeunit 50100 P
{
    procedure T()
    var
        A: Integer;
        C: Boolean;
    begin
#if X
        F();
        End;
        if C then
#endif
        A := 1;
    end;

    procedure F()
    begin
    end;
}
