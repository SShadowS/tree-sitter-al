// B7a Task 10 witness (GAP): family link-list-comma-leading, base placement adjacent-indep, 9 cells; representative occ:_link_value_run:0.1.0.0@preproc_conditional_link_values#adjacent-indep+comments@SubPageLink
// Fixture b7_gap_link_list_comma_leading_test.txt#B7a GAP: link-list-comma-leading / adjacent-indep (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_link_value_run:0.1.0.0@preproc_conditional_link_values%23adjacent-indep+comments@SubPageLink#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_link_value_run:0.1.0.0@preproc_conditional_link_values#adjacent-indep+comments@SubPageLink in tools/b7_audit/evidence.jsonl.gz
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
/* c */ , N = const(1) // c
#endif
#if Y
/* c */ , "B" = const(true) // c
#endif
/* c */ , // c

#endif
                    B = const(true);
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
