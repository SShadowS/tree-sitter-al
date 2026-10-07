// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family link-list, base placement holes-mid, 15 cells; representative occ:_link_value_branch:0.0@preproc_conditional_link_values#holes-mid+comments@SubPageLink
// Fixture b7_gap_link_list_test.txt#B7a REJECTED/over-accepts(syntax): link-list / holes-mid (15 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0292) but the parser is clean; representative occ:_link_value_branch:0.0@preproc_conditional_link_values%23holes-mid+comments@SubPageLink#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0104,AL0107,AL0292)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_link_value_branch:0.0@preproc_conditional_link_values#holes-mid+comments@SubPageLink in tools/b7_audit/evidence.jsonl.gz
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
                SubPageLink = K = field(K)
#if TPL
                    
/* c */ , // c
N = const(1) /* c */ , // c
#if X
/* c */ , // c
#endif
"B" = const(true) // c

#endif
                    ;
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
