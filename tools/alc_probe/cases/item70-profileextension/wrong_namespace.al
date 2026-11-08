// expect: * reject(AL0791)
// source: deferred item 70 negative control, recorded by batch1/probes 2026-11-08: the qualifier is resolved, not ignored (AL0791 "The namespace 'Purchasing' is unknown")
namespace Contoso.Sales;

page 50100 "My RC"
{
    PageType = RoleCenter;
}

profile "BASE PROF"
{
    Caption = 'Base';
    RoleCenter = "My RC";
}

profileextension "EXT PROF" extends Contoso.Purchasing."BASE PROF"
{
}
