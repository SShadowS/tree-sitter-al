// B7a Task 10 witness (GAP): family value-header, base placement first-replace, 3 cells; representative occ:enum_value_declaration:3@declaration_body#first-replace
// Fixture b7_gap_value_header_test.txt#B7a GAP: value-header / first-replace (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:enum_value_declaration:3@declaration_body%23first-replace#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:enum_value_declaration:3@declaration_body#first-replace in tools/b7_audit/evidence.jsonl.gz
enum 50108 En
{
    value(
#if X
0
#else
0
#endif
; V0
) { }
}
