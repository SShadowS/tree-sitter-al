// B13 (deferred item 37): a directive-only group before an OptionMembers list (read as the list's own element group).
// source: docs/deferred-work.md item 37
// expect: * accept
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
#endif
    A, B;
} } }
