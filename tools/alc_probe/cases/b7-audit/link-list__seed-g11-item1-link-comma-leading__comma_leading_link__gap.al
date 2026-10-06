// B7a Task 10 witness (GAP): family link-list, base placement seed:g11-item1-link-comma-leading__comma_leading_link, 1 cells; representative seed:g11-item1-link-comma-leading__comma_leading_link
// Fixture b7_gap_link_list_test.txt#B7a GAP: link-list / seed:g11-item1-link-comma-leading__comma_leading_link (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:g11-item1-link-comma-leading__comma_leading_link#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:g11-item1-link-comma-leading__comma_leading_link in tools/b7_audit/evidence.jsonl.gz
table 50101 Q
{
    fields { field(1; B; Integer) { } field(2; D; Integer) { } field(3; F; Integer) { } }
}
page 50100 P
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
            part(L; S)
            {
                SubPageLink = B = field(A)
#if X
                    , D = field(C)
#endif
                    , F = field(E);
            }
        }
    }
}
page 50101 S
{
    SourceTable = Q;
    layout { area(Content) { field(B; Rec.B) { } } }
}
table 50100 T
{
    fields { field(1; A; Integer) { } field(2; C; Integer) { } field(3; E; Integer) { } }
}
