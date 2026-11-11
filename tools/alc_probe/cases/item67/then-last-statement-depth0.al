// expect: * accept
// source: state review C3 review F1, deferred item 106: an empty group after `then`, the then-branch block the body's last statement (no `;`), at depth 0; main and the tip read the group as the then-branch and the block as a sibling
codeunit 50100 P
{
    procedure T()
    var
        A: Integer;
        C: Boolean;
    begin
        A := 1;
        if C then
#if Y
#endif
        begin
            A := 2;
        end
    end;
}
