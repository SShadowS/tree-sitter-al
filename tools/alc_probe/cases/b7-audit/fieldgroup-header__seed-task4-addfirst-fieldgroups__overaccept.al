// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family fieldgroup-header, base placement seed:task4-addfirst-fieldgroups, 1 cells; representative seed:task4-addfirst-fieldgroups
// Fixture b7_gap_fieldgroup_header_test.txt#B7a REJECTED/over-accepts(syntax): fieldgroup-header / seed:task4-addfirst-fieldgroups (1 cells, verdict of the representative REJECTED/over-accepts); alc rejects with a syntax code (AL0104,AL0198) but the parser is clean; representative seed:task4-addfirst-fieldgroups#0
// expect: * reject(AL0104,AL0198)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:task4-addfirst-fieldgroups in tools/b7_audit/evidence.jsonl.gz
table 50100 T { fields { field(1; N; Integer) { } } }
tableextension 50101 TE extends T
{
    fieldgroups
    {
        addfirst(DropDown; N) { }
    }
}
