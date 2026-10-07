// Pre-existing gap, NOT B7b-1 (owned by docs/deferred-work.md, recorded by Task 14): attribute inside a group, name after `#endif` (the attribute's lookahead declines at `#endif` with no `#if`). alc accepts it in every configuration; the parser does not.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
#if X
        [NonDebuggable]
#endif
        A: Integer;

    procedure Q()
    begin
    end;
}
