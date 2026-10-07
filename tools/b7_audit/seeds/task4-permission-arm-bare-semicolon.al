// host: preproc_conditional_permissions
// valid: *
// source: B7a Task 4 incidental (a `,`-led permission arm ending in a bare `;`; the parser ERRORs, alc accepted at Task 4 probe, re-measured by Task 6)
table 50100 T { fields { field(1; K; Integer) { } } }
table 50101 T2 { fields { field(1; K; Integer) { } } }
permissionset 50102 PS
{
    Assignable = true;
    Permissions = tabledata T = R
#if X
        , tabledata T2 = R;
#else
        ;
#endif
}
