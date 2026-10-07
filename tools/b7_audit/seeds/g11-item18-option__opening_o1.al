// host: option_member_list
// valid: *
// seed-source: tools/alc_probe/cases/g11-item18-option/opening_o1.al (verdicts measured by alc, as recorded in its expect lines)
// expect: * accept
// source: docs/deferred-work.md item 18 (option-member list), commit 6fed757: alc ACCEPT in every configuration, split and flat
table 50100 T
{
    fields
    {
        field(1; F; Option)
        {
            OptionMembers =
#if X
                A,
#endif
                B, C;
        }
    }
}
