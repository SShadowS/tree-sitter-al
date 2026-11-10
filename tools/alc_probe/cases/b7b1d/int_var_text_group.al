// probe: item 88: a text-bearing group after a type that is not Label: valid only inactive.
// expect: !X accept
// expect: X reject(AL0104,AL0107)
// source: B7b-1d review, 2026-11-10, measured with tools.alc_probe.
codeunit 50100 C
{
    var
        A: Integer
#if X
        'a', Locked = true
#endif
        ;
}
