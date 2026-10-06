// B6 (_expression_statement narrowing): parenless keyword-identifier statement
// source: B6 final review, 2026-10-06; was a keyword_identifier statement on main
// expect: * reject(AL0117)
codeunit 50101 Probe
{
    procedure Main()
    begin
        Session;
    end;
}
