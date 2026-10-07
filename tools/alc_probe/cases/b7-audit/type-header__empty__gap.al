// B7a Task 10 witness (GAP): family type-header, base placement empty, 3 cells; representative occ:type_declaration:3@assembly_body#empty
// Fixture b7_gap_type_header_test.txt#B7a GAP: type-header / empty (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:type_declaration:3@assembly_body%23empty#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:type_declaration:3@assembly_body#empty in tools/b7_audit/evidence.jsonl.gz
dotnet
{
    assembly(mscorlib)
    {
        type(
System.Text.StringBuilder ;
#if X
#endif
SB
) { }
    }
}
