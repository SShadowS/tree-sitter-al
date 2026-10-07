// B7a Task 10 witness (GAP): family interface-procedure, base placement sep-only, 3 cells; representative occ:interface_procedure_suffix:2@interface_procedure#sep-only
// Fixture b7_gap_interface_procedure_test.txt#B7a GAP: interface-procedure / sep-only (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:interface_procedure_suffix:2@interface_procedure%23sep-only#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:interface_procedure_suffix:2@interface_procedure#sep-only in tools/b7_audit/evidence.jsonl.gz
interface IQ
{
    
procedure Z()
#if X
;
#else
;
#endif

}
