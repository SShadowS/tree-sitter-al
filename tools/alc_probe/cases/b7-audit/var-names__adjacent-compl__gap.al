// B7a Task 10 witness (GAP): family var-names, base placement adjacent-compl, 9 cells; representative occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#adjacent-compl
// Fixture b7_gap_var_names_test.txt#B7a GAP: var-names / adjacent-compl (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:variable_declaration:2.0.1.0.0@preproc_conditional_var%23adjacent-compl#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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
        
X1
#if X
, X2
#endif
#if not X
, "X 6"
#endif
: Integer;
#endif
}
