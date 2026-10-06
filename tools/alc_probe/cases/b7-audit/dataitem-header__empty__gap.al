// B7a Task 10 witness (GAP): family dataitem-header, base placement empty, 6 cells; representative occ:_report_dataitem_header:3@report_dataitem#empty
// Fixture b7_gap_dataitem_header_test.txt#B7a GAP: dataitem-header / empty (6 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_report_dataitem_header:3@report_dataitem%23empty#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_report_dataitem_header:3@report_dataitem#empty in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
report 50106 Rp
{
    ProcessingOnly = true;
    dataset
    {
        dataitem(
D ;
#if X
#endif
T
)
        {
            column(K; K) { }
        }
    }
}
