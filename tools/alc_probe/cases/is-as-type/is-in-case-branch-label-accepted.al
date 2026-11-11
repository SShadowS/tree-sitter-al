// probe: `is` in a case branch label: `I is IFoo:` and `I is IFoo, B:` (ERROR on main and C2; deferred item 105)
// source: state review C2 review (scratchpad rvC2/probes2/case_is.al)
// expect: * accept
codeunit 50100 P
{
    procedure T(I: Interface IFoo)
    var
        B: Boolean;
        J: Interface IFoo;
    begin
        case true of I is IFoo: ; end;
        case true of I is IFoo, B: ; end;
    end;
}
interface IFoo
{
    procedure X();
}

