// B8: CalcFormula whole-value #if -- nested.
// source: roadmap B8, deferred-work item 16 (CalcFormula whole-value #if)
// expect: * accept
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
#if Y
                sum(S.A)
#else
                max(S.A)
#endif
#else
                lookup(S.A)
#endif
                ;
        }
    }
}
