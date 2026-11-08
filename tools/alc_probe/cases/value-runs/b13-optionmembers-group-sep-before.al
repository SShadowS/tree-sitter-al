// B13 (deferred item 37): an OptionMembers group holding `, B` after the first member, `;` after the group.
// source: docs/deferred-work.md item 37
// expect: * accept
table 50100 T { fields { field(1; K; Option) {
OptionMembers = A
#if X
    , B
#endif
    ;
} } }
