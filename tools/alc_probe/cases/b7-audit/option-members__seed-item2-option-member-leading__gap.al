// B7a Task 10 witness (GAP): family option-members, base placement seed:item2-option-member-leading, 1 cells; representative seed:item2-option-member-leading
// Fixture b7_gap_option_members_test.txt#B7a GAP: option-members / seed:item2-option-member-leading (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:item2-option-member-leading#0
// expect: !FOO accept
// expect: FOO accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:item2-option-member-leading in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; F; Option)
        {
            OptionMembers = X
#if FOO
                , Y
#endif
                ;
        }
    }
}
