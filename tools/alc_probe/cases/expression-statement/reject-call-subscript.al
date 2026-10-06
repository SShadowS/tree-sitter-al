// B6 (_expression_statement narrowing): reject-call-subscript, `Foo()[1];` (a subscript of a call)
// source: B6 task 7, 2026-10-06; the REJECT case of tools/config_oracle/tests/test_expression_statement.py without evidence until now
// expect: * reject(AL0117)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Text begin exit('ab'); end;
    procedure Main()
    begin
        Foo()[1];
    end;
}
