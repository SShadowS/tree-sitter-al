// B7b-1c (deferred item 90): a TextConst whose `;` stands inside every arm. alc accepts every configuration, split and flat; the parser ERRORs (item 90).
// expect: * accept
// source: B7b-1c review, measured with tools.alc_probe, 2026-11-10
codeunit 50100 C
{
    var
        T: TextConst
#if X
            ENU = 'a';
#else
            DAN = 'b';
#endif
}
