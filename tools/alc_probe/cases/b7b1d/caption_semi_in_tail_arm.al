// probe: item 87: a `;` inside an arm of a caption's sub-field group (the terminator in the group).
// expect: !X accept
// expect: X accept
// source: B7b-1d (deferred item 46), 2026-11-10; the parser ERRORs on this shape (item 87).
page 50100 P
{
    Caption = 'a'
#if X
        , Locked = true;
#else
        ;
#endif
    layout { }
}
