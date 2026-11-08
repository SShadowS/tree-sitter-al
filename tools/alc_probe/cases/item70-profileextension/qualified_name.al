// expect: * accept
// source: deferred item 70 / issue #36, profileextension with a namespace-qualified base name, recorded by batch1/probes 2026-11-08
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

profileextension "EXT PROF" extends Contoso.Sales."BASE PROF"
{
}
