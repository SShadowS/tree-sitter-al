// expect: * accept
// source: item 102 re-review of 75ac1db3: an empty group (and an empty group then var) after the header in a NESTED split-preamble arm, the form the oracle lowers
codeunit 50100 Demo
{
#if X
#if A
    procedure P()
#if B
#endif
#else
    procedure P(I: Integer)
#endif
#else
    procedure P(J: Text)
#endif
    begin
    end;

#if X
#if A
    trigger OnRun()
#if B
#endif
    var
        V: Integer;
#else
    trigger OnRun()
#endif
#else
    trigger OnRun()
#endif
    begin
    end;
}
