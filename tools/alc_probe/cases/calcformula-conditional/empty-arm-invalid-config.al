// B8: CalcFormula whole-value #if -- decide-empty-arm.
// source: roadmap B8, deferred-work item 16 (CalcFormula whole-value #if)
// expect: X accept
// expect: !X reject(AL0104,AL0107,AL0176)
table 50101 S { fields { field(1; A; Decimal) { } field(2; K; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; F; Decimal)
        {
            FieldClass = FlowField;
            CalcFormula =
#if X
                sum(S.A)
#endif
                ;
        }
    }
}
