// expect: * accept
// source: issue #34, pageextension extends <number>
table 50101 "Base Tab"
{
    fields { field(1; K; Integer) { } }
}
page 50103 "Base Page"
{
    SourceTable = "Base Tab";
}
pageextension 50104 "Repro Page Ext" extends 50103
{
}
