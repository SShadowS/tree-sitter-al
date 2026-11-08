// B13 (deferred item 37): OptionMembers on a report column (the compiler's second OptionValues host), list opened by a group.
// source: tools/alc_facts/property-hosts.tsv (OPTIONMEMBERS ReportColumn OptionValues)
// expect: * accept
table 50101 S { fields { field(1; N; Option) { OptionMembers = A,B; } } }
report 50100 R
{
    dataset
    {
        dataitem(D; S)
        {
            column(C; N)
            {
                OptionMembers =
#if X
                    A,
#endif
                    B;
            }
        }
    }
}
