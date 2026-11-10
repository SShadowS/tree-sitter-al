// B7a Task 10 witness (GAP): family label-attributes, base placement holes-mid, 24 cells; representative occ:label_declaration:3.0.0@labels_body#holes-mid
// Fixture strict_conditional_label_caption_tails_test.txt#B7b-1d report label / holes-mid#0
// expect: !X accept
// expect: X reject(AL0107)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:label_declaration:3.0.0@labels_body#holes-mid in tools/b7_audit/evidence.jsonl.gz
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
'a' ,
#if X
,
#endif
Locked = true
;
    }
}
