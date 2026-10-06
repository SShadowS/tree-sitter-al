// B7a Task 10 witness (GAP): family calc-formula, base placement trail, 27 cells; representative occ:_calc_formula_arm_t:0.3@declaration_body#trail
// Fixture b7_gap_calc_formula_test.txt#B7a GAP: calc-formula / trail (27 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_calc_formula_arm_t:0.3@declaration_body%23trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0104)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_calc_formula_arm_t:0.3@declaration_body#trail in tools/b7_audit/evidence.jsonl.gz
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(4; C; Integer)
        {
            FieldClass = FlowField;
            CalcFormula =
#if TPL
                
count(T)
#if X
;
#endif

#else
                count(T where(K = field(K)));
#endif
        }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
