// B7b-1b (deferred item 46): alc rejects an attribute on a parameter as syntax (AL0104), whatever its name; the grammar accepts the attribute bundle (parameter_list's attribute_item, an over-acceptance kept as it was). The #else arm is the control.
// expect: !A !B !C accept
// expect: !A !B C reject(AL0104,AL0107)
// expect: !A B !C reject(AL0104,AL0107)
// expect: !A B C reject(AL0104,AL0107)
// expect: A !B !C reject(AL0104,AL0107)
// expect: A !B C reject(AL0104,AL0107)
// expect: A B !C reject(AL0104,AL0107)
// expect: A B C reject(AL0104,AL0107)
// source: B7b-1b probe, measured with tools.alc_probe, 2026-11-08
codeunit 50100 P
{
#if A
    procedure Z([NonDebuggable] B: Integer)
#elif B
    procedure Z([Optional] B: Integer)
#elif C
    procedure Z([Mandatory] B: Integer)
#else
    procedure Z(B: Integer)
#endif
    begin
    end;
}
