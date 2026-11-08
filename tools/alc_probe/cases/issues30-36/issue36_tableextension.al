// expect: * accept
// source: issue #36, tableextension with a namespace-qualified name
namespace Contoso.Sales;

table 50100 Customer
{
    fields { field(1; "No."; Code[20]) { } }
}

tableextension 50101 "Cust Ext" extends Contoso.Sales.Customer
{
    fields { field(50100; Extra; Integer) { } }
}
