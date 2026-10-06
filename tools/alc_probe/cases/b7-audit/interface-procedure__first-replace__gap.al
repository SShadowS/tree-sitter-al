// B7a Task 10 witness (GAP): family interface-procedure, base placement first-replace, 9 cells; representative occ:interface_procedure_suffix:0.1.0@interface_procedure#first-replace
// Fixture b7_gap_interface_procedure_test.txt#B7a GAP: interface-procedure / first-replace (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:interface_procedure_suffix:0.1.0@interface_procedure%23first-replace#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:interface_procedure_suffix:0.1.0@interface_procedure#first-replace in tools/b7_audit/evidence.jsonl.gz
interface IQ
{
    
#if X
procedure Z(): Integer
#else
procedure Z(): Integer
#endif
;

}
