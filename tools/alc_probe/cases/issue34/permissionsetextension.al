// expect: * reject(AL0653)
// source: issue #34, permissionsetextension extends <number>: rejected, while the same by name compiles (_name.al)
permissionset 50109 "Base PS"
{
    Assignable = true;
}
permissionsetextension 50110 "Repro PS Ext" extends 50109
{
}
