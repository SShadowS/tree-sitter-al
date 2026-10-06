// B7a Task 10 witness (GAP): family interface-procedure, base placement nested, 3 cells; representative occ:interface_procedure_suffix:2@interface_procedure#nested
// Fixture b7_gap_interface_procedure_test.txt#B7a GAP: interface-procedure / nested (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:interface_procedure_suffix:2@interface_procedure%23nested#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:interface_procedure_suffix:2@interface_procedure#nested in tools/b7_audit/evidence.jsonl.gz
interface IQ
{
    
procedure Z()
#if X
#if Y
;
#else
;
#endif
#else
;
#endif

}
