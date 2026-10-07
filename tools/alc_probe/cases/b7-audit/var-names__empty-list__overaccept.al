// B7b-1 Task 13 witness (REJECTED/over-accepts(syntax)): family var-names, base placement empty-list, 9 cells; representative occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#empty-list (the B7a GAP witness of this shape, renamed: the strict list parses every configuration, alc still rejects one)
// Fixture strict_conditional_var_names_test.txt#strict var names MIXED: the whole name list in one group, no %23else (empty-list)#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X reject(AL0104,AL0198)
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#empty-list in tools/b7_audit/evidence.jsonl.gz
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
X1 , X2
#endif
: Integer;
#endif
}
