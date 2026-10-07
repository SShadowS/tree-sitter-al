// B7a Task 10 witness (GAP): family field-header, base placement empty, 9 cells; representative occ:_field_header:3@preproc_split_field#empty
// Fixture b7_gap_field_header_test.txt#B7a GAP: field-header / empty (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_field_header:3@preproc_split_field%23empty#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_field_header:3@preproc_split_field#empty in tools/b7_audit/evidence.jsonl.gz
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
page 50102 PG
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
            field(N; Rec.N) { }
#if TPL
            field(
N2 ;
#if X
#endif
Rec.N
)
#else
            field(N3; Rec.N)
#endif
            {
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
