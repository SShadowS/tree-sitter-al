// B7b-1e (deferred item 80): an all-empty #if group as the LAST thing in a variable's Option type (after a member, and as the whole list), before the `;`. alc accepts both configurations; the parser ERRORs on both (main and B7b-1e): an option type's list takes an all-empty group only when more of the list follows.
// expect: * accept
// source: B7b-1e probe, measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        V: Option A, B
#if X
#endif
            ;
        W: Option
#if X
#endif
            ;
}
