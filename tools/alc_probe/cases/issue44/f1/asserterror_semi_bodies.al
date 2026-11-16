// An every-arm-`;` call as the body of a decorated loop / if under asserterror (_semi_asserterror_statement).
// 78a59e78 and bc862313 read the empty group as the loop body and the call as a sibling, clean and wrong.
// expect: * accept
// source: reviewer probe rv44b/probes/one/a1_asserterror_deco.al; recorded 2026-11-15, alc 18.0.41
codeunit 50100 T
{
    procedure Q1(C: Boolean)
    begin
        asserterror while C do
#if D
#endif
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        Bar();
    end;

    procedure Q2(C: Boolean; Rec: Codeunit T)
    begin
        asserterror if C then
#if D
#endif
            with Rec do
                V(1,
#if A
              1.0);
#else
              2.0);
#endif
        Bar();
    end;

    procedure Q3()
    begin
        asserterror V(1,
#if A
              1.0);
#else
              2.0);
#endif
        Bar();
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure Bar()
    begin
    end;
}
