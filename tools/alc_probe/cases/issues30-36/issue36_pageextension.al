// expect: * accept
// source: issue #36, pageextension with a namespace-qualified name
namespace Contoso.Sales;

table 50100 Customer
{
    fields { field(1; "No."; Code[20]) { } }
}

page 50102 "Cust Page"
{
    SourceTable = Customer;
}

pageextension 50104 "Cust Page Ext" extends Contoso.Sales."Cust Page"
{
}
