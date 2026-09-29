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
