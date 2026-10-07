// B7b-1 Task 2 var-name attribute probe (spec 5.1): escaped-quote names, one holding a colon and a comma, in and around the group
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        "X""Y"
#if X
        , "P"":,Q"
#endif
        , Z: Text;

    procedure Q()
    begin
    end;
}
