// Fixture property_value_run_test.txt#B11: CalcFormula `;`-after run ending in a terminated group, then an empty group and `;`: the property ends at the group (spec 3.2)#0
// B11 controller ruling (Task 5 review), CalcFormula: a `;`-after run ending in a terminated group, then an empty group and `;`.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 3.2
// expect: * accept
// expect: X reject(AL0104,AL0124)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(3; Amount; Decimal) { } field(5; Qty; Integer) { } } }
table 50100 T { fields { field(1; K; Code[20]) { } field(2; F; Decimal) { FieldClass = FlowField;
CalcFormula =
#if X
    sum(Cust.Amount)
#endif
#if not X
    max(Cust.Amount);
#else
    min(Cust.Amount);
#endif
#if Z
#endif
;
} } }
