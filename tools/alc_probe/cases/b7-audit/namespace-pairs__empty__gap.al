// B7a Task 10 witness (GAP): family namespace-pairs, base placement empty, 9 cells; representative occ:namespace_value_list:0.1.0.0@declaration_body#empty
// Fixture b7_gap_namespace_pairs_test.txt#B7a GAP: namespace-pairs / empty (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:namespace_value_list:0.1.0.0@declaration_body%23empty#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:namespace_value_list:0.1.0.0@declaration_body#empty in tools/b7_audit/evidence.jsonl.gz
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
        
p = 'urn:a' ,
#if X
#endif
q = 'urn:b'
;
#else
        p = 'urn:c';
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
