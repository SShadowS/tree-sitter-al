// B11: B13 shape: an OptionMembers conditional member, then `, B;` outside the group (Task 9, deferred-work B13).
// source: docs/deferred-work.md B13
// expect: * accept
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
    A
#endif
    , B;
} } }
