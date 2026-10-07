// B7b-1 Task 2 route cardinality (spec 4.2): route key-fields / addfirst_fieldgroup_modification (pseudo route, hand copy of the addlast cell with addfirst); X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:field_list:1.0.0@addlast_fieldgroup_modification#empty-list.
// Measured: alc has no addfirst in fieldgroups (AL0104 also on the non-empty control), so this route has no attributable empty verdict.
// expect: !X reject(AL0104,AL0198)
// expect: X reject(AL0104,AL0198)
// source: predicted by B7b-1 Task 2 from the addlast route, measured with tools.alc_probe, 2026-10-07
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
    fieldgroups
    {
        fieldgroup(DropDown; K) { }
    }
}
tableextension 50110 TE extends T
{
    fieldgroups
    {
        addfirst(DropDown; 
#if X
N , B
#endif
) { }
    }
}
