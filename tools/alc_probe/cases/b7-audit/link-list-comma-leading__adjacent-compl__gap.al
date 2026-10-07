// B7a Task 10 witness (GAP): family link-list-comma-leading, base placement adjacent-compl, 63 cells; representative occ:_link_arm_t:0.1@declaration_body#adjacent-compl+comments@SubPageLink
// Fixture b7_gap_link_list_comma_leading_test.txt#B7a GAP: link-list-comma-leading / adjacent-compl (63 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_link_arm_t:0.1@declaration_body%23adjacent-compl+comments@SubPageLink#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_link_arm_t:0.1@declaration_body#adjacent-compl+comments@SubPageLink in tools/b7_audit/evidence.jsonl.gz
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
page 50102 PG
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
            field(N; Rec.N) { }
            part(P1; PartPg)
            {
                SubPageLink =
#if TPL
                    
K = field(K) // c
#if X
/* c */ ; // c
#endif
#if not X
/* c */ ; // c
#endif

#else
                    N = field(N);
#endif
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
page 50104 PartPg
{
    PageType = ListPart;
    SourceTable = T;
    layout
    {
        area(Content)
        {
            repeater(G)
            {
                field(K; Rec.K) { }
            }
        }
    }
}
