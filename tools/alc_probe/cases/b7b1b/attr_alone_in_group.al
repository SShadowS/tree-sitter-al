// B7b-1b (deferred item 46): an attribute alone in a group, the parameter after #endif. The parser ERRORs (an arm holds only whole parameters and separators). alc accepts only the configuration without the attribute: a parameter attribute is a syntax error (param_attribute_flat.al).
// expect: !X accept
// expect: X reject(AL0104,AL0107,AL0301)
// source: B7b-1b probe, measured with tools.alc_probe, 2026-11-08
codeunit 50100 P
{
    procedure Z(A: Integer;
#if X
        [NonDebuggable]
#endif
        B: Integer)
    begin
    end;
}
