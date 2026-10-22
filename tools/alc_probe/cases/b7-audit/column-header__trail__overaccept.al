// B7b-2 Task 12 witness (REJECTED/over-accepts(syntax)): family column-header, base placement trail, 9 cells; representative occ:report_column:3@report_body#trail
// Fixture b7_gap_column_header_test.txt#B7a GAP: column-header / trail (15 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:query_column:2.0.1@query_body%23trail#0
// expect: !X reject(AL0104,AL0224)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:report_column:3@report_body#trail in tools/b7_audit/evidence.jsonl.gz; the group is OVERACCEPT since B7b-2 Phase C parses the split tree clean (Task 12)
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
        dataitem(D; T)
        {
            column(
K ;
#if X
K
#endif
) { }
        }
    }
}
