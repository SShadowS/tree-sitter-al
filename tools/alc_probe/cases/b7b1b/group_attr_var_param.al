// B7b-1b (deferred item 46): a group holding a whole `var` parameter between two separators, with an #elif arm; a leading group whose arm ends with the separator before a quoted `""` name; a group with the separator before its parameter at the end of an event's list. alc accepts every configuration. (No attribute: alc rejects any parameter attribute as syntax, AL0104; see param_attribute_flat.al.)
// expect: * accept
// source: B7b-1b probe, measured with tools.alc_probe, 2026-11-08
codeunit 50100 P
{
    procedure Z(A: Integer;
#if X
        var B: Integer;
#elif Y
        var B: Text;
#endif
        C: Integer)
    begin
    end;

    procedure W(
#if X
        A: Integer;
#endif
        var "B ""q""": Code[20])
    begin
    end;

    [IntegrationEvent(false, false)]
    procedure OnE(A: Integer
#if Y
        ; B: Boolean
#endif
    )
    begin
    end;
}
