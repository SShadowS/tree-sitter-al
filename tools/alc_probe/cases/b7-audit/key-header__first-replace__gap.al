// B7a Task 10 witness (GAP): family key-header, base placement first-replace, 3 cells; representative occ:_key_header:3@key_declaration#first-replace
// Fixture b7_gap_key_header_test.txt#B7a GAP: key-header / first-replace (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_key_header:3@key_declaration%23first-replace#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_key_header:3@key_declaration#first-replace in tools/b7_audit/evidence.jsonl.gz
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
        key(
#if X
SK
#else
SK
#endif
; N
) { }
    }
}
