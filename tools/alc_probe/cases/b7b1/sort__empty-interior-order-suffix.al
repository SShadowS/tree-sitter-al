// B7b-1 Task 7 route sorting-fields (spec 4.2): sorting() emptied by X undefined, followed by an order(...) suffix.
// expect: * accept
// source: predicted by B7b-1 Task 7 review (4th sorting_value arm), measured with tools.alc_probe, 2026-10-07
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
page 50102 PG
{
    SourceTable = T;
    SourceTableView = sorting(
#if X
K
#endif
) order(descending);
    layout
    {
        area(Content)
        {
            field(N; Rec.N) { }
        }
    }
}
