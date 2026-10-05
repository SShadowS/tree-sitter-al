// B8: CalcFormula whole-value #if -- decide-tableext-modify.
// source: roadmap B8, deferred-work item 16 (CalcFormula whole-value #if)
// expect: * reject(AL0171)
table 50101 S { fields { field(1; A; Decimal) { } field(2; K; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; F; Decimal) { FieldClass = FlowField; CalcFormula = sum(S.A); }
    }
}
tableextension 50100 TX extends T
{
    fields
    {
        modify(F)
        {
            CalcFormula =
#if X
                sum(S.A)
#else
                max(S.A)
#endif
                ;
        }
    }
}
