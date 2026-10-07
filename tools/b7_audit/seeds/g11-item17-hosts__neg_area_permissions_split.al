// host: permissions_property
// valid: none
// seed-source: tools/alc_probe/cases/g11-item17-hosts/neg_area_permissions_split.al (verdicts measured by alc, as recorded in its expect lines)
// expect: * reject(AL0124)
// source: docs/deferred-work.md item 17 and commit 04af3f6: Permissions at the host REJECT (AL0124), flat and split
table 50101 TT { fields { field(1; A; Integer) { } } }

page 50100 P
{
    PageType = RoleCenter;
    actions
    {
        area(Embedding)
        {
            Permissions =
#if X
                    tabledata TT = R;
#else
                    tabledata TT = RM;
#endif
            action(A) { RunObject = page P; }
        }
    }
}
