// Pre-existing gap, NOT B7b-1 (owned by docs/deferred-work.md, recorded by Task 14): attribute, then whole declarations in the arms of a group (the var_attribute_open lookahead declines at the `:` inside the group). alc accepts it in every configuration; the parser does not.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
        A: Integer;
#else
        B: Integer;
#endif

    procedure Q()
    begin
    end;
}
