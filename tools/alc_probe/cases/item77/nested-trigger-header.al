// expect: * accept
// source: deferred item 85 (from item 77's review): a nested #if choosing a TRIGGER header, the trigger counterpart of item 77
codeunit 50100 P
{
#if X
#if Y
    trigger OnRun()
#else
    trigger OnRun()
#endif
#else
    trigger OnRun()
#endif
    begin
    end;
}
