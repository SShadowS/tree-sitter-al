// B7a Task 10 witness (GAP): family table-relation, base placement seed:g11-item19-relation__neg_two_tables_after_else, 1 cells; representative seed:g11-item19-relation__neg_two_tables_after_else
// Fixture b7_gap_table_relation_test.txt#B7a GAP: table-relation / seed:g11-item19-relation__neg_two_tables_after_else (1 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative seed:g11-item19-relation__neg_two_tables_after_else#0
// expect: !X accept
// expect: X reject(AL0104,AL0124)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:g11-item19-relation__neg_two_tables_after_else in tools/b7_audit/evidence.jsonl.gz
table 50101 Item { fields { field(1; "No."; Code[20]) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; Type; Option) { OptionMembers = Item, Resource; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
#if X
                else Resource Customer
#endif
                ;
        }
    }
}
