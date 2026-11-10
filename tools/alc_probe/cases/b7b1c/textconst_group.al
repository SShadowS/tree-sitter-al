// B7b-1c: a TextConst variable's language list with groups at the separators, including a list that is only groups.
// expect: * accept
// source: B7b-1c probe, measured with tools.alc_probe, 2026-11-10
codeunit 50100 C
{
    var
        T1: TextConst ENU = 'a'
#if X
            , DAN = 'b'
#endif
            ;
        T2: TextConst
#if X
            ENU = 'a',
#endif
            DAN = 'b';
        T3: TextConst
#if X
            ENU = 'a'
#else
            DAN = 'b'
#endif
            ;
}
