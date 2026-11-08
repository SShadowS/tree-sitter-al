// expect: * accept
// source: issue #36, implements with a namespace-qualified name
namespace Contoso.Sales;

interface IFoo
{
    procedure Foo();
}

interface IBar
{
    procedure Bar();
}

codeunit 50103 Impl implements Contoso.Sales.IFoo, IBar
{
    procedure Foo()
    begin
    end;

    procedure Bar()
    begin
    end;
}
