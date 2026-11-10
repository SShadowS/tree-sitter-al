// B7b-1c (deferred item 90): a `;` group after a keyed value, at the property and inside a whole-value arm. alc accepts every configuration; the parser ERRORs (item 90).
// expect: * accept
// source: B7b-1c probe, measured with tools.alc_probe, 2026-11-10
page 50100 P
{
    CaptionML = ENU = 'a'
#if X
    ;
#else
    ;
#endif
    AdditionalSearchTermsML =
#if X
        ENU = 'a'
#if Y
        ;
#else
        ;
#endif
#else
        ENU = 'b';
#endif
}
