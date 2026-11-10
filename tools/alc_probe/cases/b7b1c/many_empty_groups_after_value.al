// B7b-1c (deferred item 91): 9 empty groups after a keyed value, and after a whole-value group. alc accepts; on the branch the first groups of such a run are list groups (the threshold in the corpus fixtures), a tree-shape change on valid input.
// expect: * accept
// source: B7b-1c review, measured with tools.alc_probe, 2026-11-10
page 50100 P
{
    CaptionML = ENU = 'a'
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
        ;
    AdditionalSearchTermsML =
#if X
        ENU = 'a'
#else
        ENU = 'b'
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
        ;
}
xmlport 50101 X
{
    Namespaces = a = 'urn:a'
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
#if Y
#endif
        ;
    schema
    {
        textelement(R) { }
    }
}
