// expect: * accept
// source: issue #36, permissionsetextension with a namespace-qualified name
namespace Contoso.Sales;

permissionset 50109 "Base PS"
{
    Assignable = true;
}

permissionsetextension 50110 "PS Ext" extends Contoso.Sales."Base PS"
{
}
