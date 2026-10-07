// B7b-1 Task 2 var-name attribute probe (spec 5.1): Unicode names and contextual-keyword names in the group
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        Æble
#if X
        , Value, Table, Field
#endif
        , Ørn: Text;

    procedure Q()
    begin
    end;
}
