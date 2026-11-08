// expect: * accept
// source: issue #36, enumextension with a namespace-qualified name
namespace Contoso.Sales;

enum 50105 "Base Enum"
{
    Extensible = true;
    value(0; A) { }
}

enumextension 50106 "Enum Ext" extends Contoso.Sales."Base Enum"
{
    value(50100; B) { }
}
