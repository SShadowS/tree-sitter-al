// B7a Task 10 witness (GAP): family var-declaration, base placement first-replace, 36 cells; representative occ:variable_declaration:0.0.5@preproc_conditional_var#first-replace
// Fixture b7_gap_var_declaration_test.txt#B7a GAP: var-declaration / first-replace (36 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:variable_declaration:0.0.5@preproc_conditional_var%23first-replace#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:variable_declaration:0.0.5@preproc_conditional_var#first-replace in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
codeunit 50101 P
{
    var
#if TPL2
        
#if X
Lbl: Label 'a'
#else
Lbl: Label 'a'
#endif
;

#endif
}
