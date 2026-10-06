// B7a Task 10 witness (GAP): family namespace-pairs, base placement holes-trail, 9 cells; representative occ:namespace_value_list:0.1.0.0@declaration_body#holes-trail
// Fixture b7_gap_namespace_pairs_test.txt#B7a GAP: namespace-pairs / holes-trail (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:namespace_value_list:0.1.0.0@declaration_body%23holes-trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:namespace_value_list:0.1.0.0@declaration_body#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
        
p = 'urn:a' , q = 'urn:b'
#if X
,
#endif
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
