// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family where-filter, base placement empty-list, 3 cells; representative occ:_where_run:0.1.0.0@where_conditions#empty-list
// Fixture b7_gap_where_filter_test.txt#B7a REJECTED/over-accepts(syntax): where-filter / empty-list (3 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0292) but the parser is clean; representative occ:_where_run:0.1.0.0@where_conditions%23empty-list#0
// expect: !X reject(AL0104,AL0107,AL0292)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_where_run:0.1.0.0@where_conditions#empty-list in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; C; Integer)
        {
            FieldClass = FlowField;
            CalcFormula = count(T where(
#if X
K = field(K) , N = const(1)
#endif
));
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
