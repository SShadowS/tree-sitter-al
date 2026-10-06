// B7a Task 10 witness (GAP): family label-attributes, base placement holes-trail, 24 cells; representative occ:label_declaration:3.0.0@labels_body#holes-trail
// Fixture b7_gap_label_attributes_test.txt#B7a GAP: label-attributes / holes-trail (24 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:label_declaration:3.0.0@labels_body%23holes-trail#0
// expect: !X accept
// expect: X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:label_declaration:3.0.0@labels_body#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
        L1 = 
'a' , Locked = true
#if X
,
#endif
;
    }
}
