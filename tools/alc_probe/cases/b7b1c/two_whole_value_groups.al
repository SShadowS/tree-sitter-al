// B7b-1c: two whole-value ML groups with the `;` after the last #endif (the preservation fixture "ML two whole-value groups"): each single arm is a one-pair value; X and Y together put two pairs side by side, which alc rejects.
// Fixture strict_conditional_pair_lists_test.txt#strict pair list: ML two whole-value groups, `;` after the last %23endif (preservation: the sequence, not a list group)#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y reject(AL0104)
// source: B7b-1c probe, measured with tools.alc_probe, 2026-11-10
page 50100 P
{
    CaptionML =
#if X
        ENU = 'a'
#endif
#if Y
        DAN = 'b'
#endif
        ;
}
