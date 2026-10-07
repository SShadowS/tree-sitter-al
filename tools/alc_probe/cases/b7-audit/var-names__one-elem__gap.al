// B7a Task 10 witness (GAP): family var-names, base placement one-elem, 9 cells; representative occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#one-elem
// Fixture strict_conditional_var_names_test.txt#strict var names: the whole name list in the arms of one group (one-elem)#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:variable_declaration:2.0.1.0.0@preproc_conditional_var#one-elem in tools/b7_audit/evidence.jsonl.gz
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
#else
X1
#endif
: Integer;
#endif
}
