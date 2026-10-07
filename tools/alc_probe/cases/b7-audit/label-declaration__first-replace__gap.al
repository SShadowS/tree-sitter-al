// B7a Task 10 witness (GAP): family label-declaration, base placement first-replace, 6 cells; representative occ:label_declaration:4@labels_body#first-replace
// Fixture b7_gap_label_declaration_test.txt#B7a GAP: label-declaration / first-replace (6 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:label_declaration:4@labels_body%23first-replace#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:label_declaration:4@labels_body#first-replace in tools/b7_audit/evidence.jsonl.gz
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
        dataitem(D; T) { }
    }
    labels
    {
        
#if X
L1 = 'a'
#else
L1 = 'a'
#endif
;

    }
}
