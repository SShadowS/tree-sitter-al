// Item 45: an attribute, then a var-section TAIL group (each arm a declaration, then a procedure). Clean before item 45 with the attribute a procedure attribute_item; now a var_attribute_item at the end of the var_body, since in every configuration it belongs to the arm's declaration. Fixture `var attribute group: declaration then procedure in each arm (var section tail)`.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
    [NonDebuggable]
#if X
    B: Integer;
    procedure Q()
    begin
    end;
#else
    C: Integer;
    procedure Q()
    begin
    end;
#endif

    procedure Z()
    begin
    end;
}
