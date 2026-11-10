// B7b-1c: the pair list of a property that is not one of the 13 keyed ML names. alc rejects it (the registry's `na` row for occ:_ml_value_list_flat): only the grammar's generic _property_value arm reads it, and no group is added there.
// expect: * reject(AL0219)
// source: B7b-1c probe, measured with tools.alc_probe, 2026-11-10
page 50100 P
{
    Caption = ENU = 'a', DAN = 'b';
}
