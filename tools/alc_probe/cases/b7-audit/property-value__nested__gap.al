// B7a Task 10 witness (GAP): family property-value, base placement nested, 162 cells; representative bnd:_property_value_with_split:0.0:end@action_body#nested/comparison
// Fixture b7_gap_property_value_test.txt#B7a GAP: property-value / nested (162 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:_property_value_with_split:0.0:end@action_body%23nested/comparison#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_property_value_with_split:0.0:end@action_body#nested/comparison in tools/b7_audit/evidence.jsonl.gz
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
        }
    }
    actions
    {
        area(Processing)
        {
            action(A1)
            {
                Visible =
#if TPL
                    
Ok
#if X
= true
#if Y
= false
#endif
#endif
;
#else
                    Ok;
#endif
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        I: Integer;
        Ok: Boolean;
}
