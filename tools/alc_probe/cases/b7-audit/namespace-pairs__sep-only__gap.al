// B7a Task 10 witness (GAP): family namespace-pairs, base placement sep-only, 36 cells; representative occ:_namespaces_arm_t:0.3@declaration_body#sep-only
// Fixture b7_gap_namespace_pairs_test.txt#B7a GAP: namespace-pairs / sep-only (36 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_namespaces_arm_t:0.3@declaration_body%23sep-only#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_namespaces_arm_t:0.3@declaration_body#sep-only in tools/b7_audit/evidence.jsonl.gz
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
xmlport 50107 Xp
{
    Namespaces =
#if TPL
        
p = 'urn:a'
#if X
;
#else
;
#endif

#else
        p = 'urn:b';
#endif
    schema
    {
        textelement(Root)
        {
            tableelement(D; T)
            {
                fieldattribute(K; D.K) { }
                fieldelement(N; D.N) { }
            }
        }
    }
}
