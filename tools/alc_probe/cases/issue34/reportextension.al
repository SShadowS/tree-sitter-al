// expect: * accept
// source: issue #34, reportextension extends <number>
report 50107 "Base Report"
{
    ProcessingOnly = true;
}
reportextension 50108 "Repro Report Ext" extends 50107
{
}
