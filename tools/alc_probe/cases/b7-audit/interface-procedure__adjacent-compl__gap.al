// B7a Task 10 witness (GAP): family interface-procedure, base placement adjacent-compl, 3 cells; representative occ:interface_procedure_suffix:2@interface_procedure#adjacent-compl
// Fixture b7_gap_interface_procedure_test.txt#B7a GAP: interface-procedure / adjacent-compl (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:interface_procedure_suffix:2@interface_procedure%23adjacent-compl#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:interface_procedure_suffix:2@interface_procedure#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
interface IQ
{
    
procedure Z()
#if X
;
#endif
#if not X
;
#endif

}
