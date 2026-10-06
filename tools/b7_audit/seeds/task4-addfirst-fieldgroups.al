// host: fieldgroups_body
// valid: none
// source: B7a Task 4 incidental (`addfirst` in a tableextension fieldgroups section: alc AL0104 at Task 4 probe; the grammar over-accepts)
table 50100 T { fields { field(1; N; Integer) { } } }
tableextension 50101 TE extends T
{
    fieldgroups
    {
        addfirst(DropDown; N) { }
    }
}
