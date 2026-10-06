// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family integer-list, base placement holes-lead, 6 cells; representative occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-lead
// No corpus case: the oracle reports a discrepancy in a configuration alc rejects; the parser side is pinned by tools/b7_audit/tests/test_silent.py
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0456)
// expect: TPL X reject(AL0107)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
                
#if X
,
#endif
-1 , 0
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
