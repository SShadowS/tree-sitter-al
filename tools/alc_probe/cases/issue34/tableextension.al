// expect: * accept
// source: issue #34, tableextension extends <number>
table 50101 "Base Tab"
{
    fields { field(1; K; Integer) { } }
}
tableextension 50102 "Repro Tab Ext" extends 50101
{
    procedure Validate(A: Integer)
    begin
    end;
}
