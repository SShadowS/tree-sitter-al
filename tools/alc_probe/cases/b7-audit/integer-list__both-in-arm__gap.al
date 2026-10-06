// B7a Task 10 witness (GAP): family integer-list, base placement both-in-arm, 9 cells; representative occ:signed_integer_list:0.0.1.0.0@declaration_body#both-in-arm
// Fixture b7_gap_integer_list_test.txt#B7a GAP: integer-list / both-in-arm (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:signed_integer_list:0.0.1.0.0@declaration_body%23both-in-arm#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0456)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:signed_integer_list:0.0.1.0.0@declaration_body#both-in-arm in tools/b7_audit/evidence.jsonl.gz
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
, 0 ,
#else
,
#endif
1
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
