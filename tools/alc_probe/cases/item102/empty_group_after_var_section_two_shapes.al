// expect: * accept
// source: item 102 re-review of 75ac1db3, deferred item 109: an empty group after a plain var section is an empty preproc_conditional_var inside var_body; after a var group it is a preproc_pragma_only (two shapes, pre-existing on dcec0b4f)
codeunit 50100 Demo
{
    procedure P()
    var
        V: Integer;
#if B
#endif
    begin
    end;

    procedure Q()
#if A
    var
        W: Integer;
#endif
#if B
#endif
    begin
    end;
}
