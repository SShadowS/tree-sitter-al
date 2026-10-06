// B7a Task 10 witness (GAP): family value-header, base placement trail, 3 cells; representative occ:enum_value_declaration:3@declaration_body#trail
// Fixture b7_gap_value_header_test.txt#B7a GAP: value-header / trail (3 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:enum_value_declaration:3@declaration_body%23trail#0
// expect: !X reject(AL0107)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:enum_value_declaration:3@declaration_body#trail in tools/b7_audit/evidence.jsonl.gz
enum 50108 En
{
    value(
0 ;
#if X
V0
#endif
) { }
}
