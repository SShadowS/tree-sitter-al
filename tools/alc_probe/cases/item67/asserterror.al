// expect: * accept
// source: deferred item 67 correction (issue #44 re-review, 2026-11-15): an empty group before an asserterror body; main read the group as the body and the call as a sibling
codeunit 50100 Demo
{
    procedure Q1()
    begin
        asserterror
#if D
#endif
            Bar();
        Bar();
    end;

    procedure Bar()
    begin
    end;
}
