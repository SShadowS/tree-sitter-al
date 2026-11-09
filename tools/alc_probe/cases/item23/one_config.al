// Deferred item 23: the list's `;` is in an arm with no #else, then a #if procedure. Valid only when X: then the list ends at #endif.
// Fixture item_23_permissions_semi_arm_follower_test.txt#Item 23: `;` in an arm with no %23else, then a %23if procedure (valid only when X)#0
// expect: X accept
// expect: !X reject(AL0104,AL0124,AL0198,AL0301)
// source: deferred item 23, 2026-11-09 (a form valid in one configuration must still parse)
codeunit 50101 P
{
    Permissions = tabledata T1 = r,
#if X
                  tabledata T2 = i;
#endif
#if X
    procedure A()
    begin
    end;
#endif
}

table 50101 T1
{
    fields
    {
        field(1; F; Integer) { }
    }
}
table 50102 T2
{
    fields
    {
        field(1; F; Integer) { }
    }
}
