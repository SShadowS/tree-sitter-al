// B7a Task 10 witness (GAP): family type-header, base placement elif, 3 cells; representative occ:type_declaration:3@assembly_body#elif
// Fixture b7_gap_type_header_test.txt#B7a GAP: type-header / elif (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:type_declaration:3@assembly_body%23elif#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:type_declaration:3@assembly_body#elif in tools/b7_audit/evidence.jsonl.gz
dotnet
{
    assembly(mscorlib)
    {
        type(
System.Text.StringBuilder
#if X
;
#elif Y
;
#else
;
#endif
SB
) { }
    }
}
