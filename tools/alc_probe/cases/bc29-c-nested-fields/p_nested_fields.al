// expect: * accept
// source: docs/bc29-parse-gaps.md family C (ACCEPT with symbols undefined and with S31,C28 defined); commit d3a2d20 says "alc accepts all four configurations"
// source: recorded by A2, 2026-09-29: S31 alone and C28 alone (d3a2d20's "all four" may mean the four-way rule, not four assignments)
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not S31
#if not C28
        field(2; B; Integer) { }
#endif
        field(3; C; Integer) { }
#endif
        field(4; D; Integer) { }
    }
}
