// expect: * accept
// source: docs/deferred-work.md item 17, commit 04af3f6: alc four-way ACCEPT (action group)
page 50100 P
{
    PageType = RoleCenter;
    actions
    {
        area(Embedding)
        {
            group(G)
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
}
