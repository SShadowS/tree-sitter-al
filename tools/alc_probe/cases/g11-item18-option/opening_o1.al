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
