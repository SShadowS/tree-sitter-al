// host: g11-item17-hosts
// valid: *
// seed-source: tools/alc_probe/cases/g11-item17-hosts/action_area_tooltip.al (verdicts measured by alc, as recorded in its expect lines)
// expect: * accept
// source: docs/deferred-work.md item 17, commit 04af3f6: alc four-way ACCEPT (area)
page 50100 P
{
    PageType = RoleCenter;
    actions
    {
        area(Embedding)
        {
            ToolTip =
#if X
                    'a';
#else
                    'b';
#endif
            action(A) { RunObject = page P; }
        }
    }
}
