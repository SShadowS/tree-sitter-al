// expect: * accept
// source: deferred item 70 control, recorded by batch1/probes 2026-11-08. The issue #36 probe failed with AL0341 "'Caption' property is missing": a profile requires Caption.
page 50100 "My RC"
{
    PageType = RoleCenter;
}

profile "BASE PROF"
{
    Caption = 'Base';
    RoleCenter = "My RC";
}

profileextension "EXT PROF" extends "BASE PROF"
{
}
