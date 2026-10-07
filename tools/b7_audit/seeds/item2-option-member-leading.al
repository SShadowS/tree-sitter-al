// host: option_member_list
// valid: *
// source: docs/deferred-work.md item 2 (the comma INSIDE the group: `X #if FOO , Y #endif`)
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
