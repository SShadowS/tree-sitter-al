// B13 (deferred item 37): a nested OptionMembers group inside a list element group.
// source: docs/deferred-work.md item 37
// expect: * accept
table 50100 T { fields { field(1; K; Option) {
OptionMembers = A,
#if X
    B,
#if Y
    C,
#endif
#endif
    D;
} } }
