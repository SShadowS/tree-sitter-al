// expect: * reject
// source: docs/deferred-work.md item 17 and commit 04af3f6: TableRelation at the host REJECT (AL0124)
table 50101 TT { fields { field(1; A; Integer) { } } }

page 50100 P
{
    PageType = RoleCenter;
    actions
    {
        area(Embedding)
        {
            TableRelation = TT;
            action(A) { RunObject = page P; }
        }
    }
}
