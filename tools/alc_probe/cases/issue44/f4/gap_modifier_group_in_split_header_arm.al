// NOT COVERED by the F4 design (deferred item 113): a modifier group INSIDE an arm of a split procedure header.
// alc accepts all four configurations; the parser ERRORs (the arm holds only a procedure head).
// expect: * accept
// source: reviewer probe rv44small/probe_f4/group_mod_in_split_arm.al; recorded 2026-11-15, alc 18.0.41
codeunit 50100 T
{
#if A
#if B
    local
#endif
    procedure P()
#else
    procedure P(I: Integer)
#endif
    begin
    end;
}
