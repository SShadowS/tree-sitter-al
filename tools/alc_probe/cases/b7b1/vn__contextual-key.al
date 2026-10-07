// B7b-1 Task 2 var-name attribute probe (spec 5.1): `Key` as a non-first name (alc rejects `Z, Key: Text;` with no attribute and no group too)
// expect: * accept
// expect: X reject(AL0104,AL0105,AL0107)
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        Z
#if X
        , Key
#endif
        : Text;

    procedure Q()
    begin
    end;
}
