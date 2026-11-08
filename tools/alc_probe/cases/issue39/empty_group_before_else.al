// expect: * accept
// source: issue #39 (invented repro)
codeunit 50100 Demo
{
    procedure Run(Ready: Boolean)
    begin
        if Ready then
            First()
#if FEATURE
#endif
        else
            Second();
        if Ready then begin
            First();
        end
#if FEATURE
#else
#endif
        else
            Second();
    end;

    local procedure First()
    begin
    end;

    local procedure Second()
    begin
    end;
}
