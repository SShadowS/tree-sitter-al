// probe: a caption's trailing comma, then an all-empty group: the shape whose tree B7b-1d changes (option_member_list -> caption_value + sibling group).
// expect: !X accept
// expect: X accept
// source: B7b-1d review, 2026-11-10, measured with tools.alc_probe.
page 50100 P
{
    Caption = 'a',
#if X
#endif
    ;
    layout { }
}
