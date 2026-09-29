// Fixture property_value_conditional_node_test.txt#G6: an empty arm has no value field#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !X reject(AL0104,AL0109)
// expect: X accept
table 50100 T
{
    fields
    {
        field(1; F; Integer)
        {
            MaxValue =
#if X
                10;
#else
#endif
        }
    }
}
