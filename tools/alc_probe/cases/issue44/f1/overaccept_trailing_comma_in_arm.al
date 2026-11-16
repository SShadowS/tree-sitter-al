// OVER-ACCEPTED by the F1 design (deferred item 44): a trailing `,` before the `)` inside a closing
// arm (the arm's argument run allows one, as in preproc_conditional_arguments, where a `,` may join
// the run to an argument after `#endif`; here a `)` always follows). The parser reads it clean.
// expect: * accept
// expect: A reject(AL0301)
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1)
codeunit 50100 T
{
    procedure P1()
    begin
        V(1,
#if A
          2,);
#else
          3);
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
