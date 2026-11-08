// B13 (deferred item 37, B11 Minor 1): two members with no separator after the groups; invalid AL in every configuration.
// Fixture option_members_keyed_negative_test.txt#B13 keyed OptionMembers: two members with no separator after the groups stay an ERROR (alc AL0104 in every configuration, b13-optionmembers-adjacent-members.al; parsed clean before the keying, B11 Minor 1)#0
// source: docs/deferred-work.md item 37 (OptionMembers adjacency over-acceptance)
// expect: * reject(AL0104)
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
    A,
#endif
#if Y
    B,
#endif
    C D;
} } }
