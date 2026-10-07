// Pre-existing gap, NOT B7b-1 (owned by docs/deferred-work.md, recorded by Task 14): second attribute inside a group before a var name (the lookahead declines at the `[` inside the group). alc accepts it in every configuration; the parser does not.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
        [NonDebuggable]
#endif
        A: Integer;

    procedure Q()
    begin
    end;
}
