// B7a Task 10 witness (GAP): family type-header, base placement sep-only, 3 cells; representative occ:type_declaration:3@assembly_body#sep-only
// Fixture b7_gap_type_header_test.txt#B7a GAP: type-header / sep-only (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:type_declaration:3@assembly_body%23sep-only#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:type_declaration:3@assembly_body#sep-only in tools/b7_audit/evidence.jsonl.gz
dotnet
{
    assembly(mscorlib)
    {
        type(
System.Text.StringBuilder
#if X
;
#else
;
#endif
SB
) { }
    }
}
