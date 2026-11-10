// probe: a caption's trailing comma, then a group holding only a `,`: inactive it is the flat `Caption = 'a',;`, active it is a second trailing comma.
// expect: !X accept
// expect: X reject(AL0107)
// source: B7b-1d review, 2026-11-10, measured with tools.alc_probe.
page 50100 P
{
    Caption = 'a',
#if X
    ,
#endif
    ;
    layout { }
}
