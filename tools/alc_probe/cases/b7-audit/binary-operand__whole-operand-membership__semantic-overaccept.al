// B7b-2 Task 12 witness (REJECTED/over-accepts(semantic)): family binary-operand, base placement whole-operand/membership, 3 cells (bnd:logical_expression:{left:end,left:start,right:end}@property_expression#whole-operand/membership); representative bnd:logical_expression:left:end@property_expression#whole-operand/membership
// expect: !X reject(AL0322)
// expect: X reject(AL0322)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:logical_expression:left:end@property_expression#whole-operand/membership in tools/b7_audit/evidence.jsonl.gz. alc rejects every configuration with the semantic AL0322 (the generator's type error, deferred-work item 42); the parser ERRORed until B7b-2 Phase C and now reads the `in` right as an operand group, clean: a semantic over-acceptance (parse structure, don't validate), no syntax defect. No corpus case: the manifest row (excluded, B7a) records it.
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
            field(N; Rec.N)
            {
                Visible =
Ok in
#if X
[true, false]
#else
[true]
#endif
 and Ok;
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
