// expect: * accept
// source: issue #34, permissionsetextension extends <name> (control)
permissionset 50109 "Base PS"
{
    Assignable = true;
}
permissionsetextension 50110 "Repro PS Ext" extends "Base PS"
{
}
