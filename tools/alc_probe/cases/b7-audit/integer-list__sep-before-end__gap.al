// B7a Task 10 witness (GAP): family integer-list, base placement sep-before-end, 6 cells; representative occ:signed_integer_list:0.0.1.0.0@declaration_body#sep-before-end
// Fixture b7_gap_integer_list_test.txt#B7a GAP: integer-list / sep-before-end (6 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:signed_integer_list:0.0.1.0.0@declaration_body%23sep-before-end#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0456)
// expect: TPL X reject(AL0456)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:signed_integer_list:0.0.1.0.0@declaration_body#sep-before-end in tools/b7_audit/evidence.jsonl.gz
table 50115 CT
{
    TableType = CRM;
    ExternalName = 'ct';
    fields
    {
        field(1; K; Code[20]) { ExternalName = 'k'; ExternalType = 'String'; }
        field(2; O2; Option)
        {
            ExternalName = 'o';
            ExternalType = 'Picklist';
            OptionMembers = A,B,C;
            OptionOrdinalValues =
#if TPL
                
-1
#if X
, 0
#endif
;
#else
                1, 2, 3;
#endif
        }
    }
    keys
    {
        key(PK; K) { }
    }
}
