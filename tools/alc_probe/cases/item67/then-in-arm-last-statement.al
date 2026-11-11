// expect: * accept
// source: state review C3 review F1: an empty group after `then` inside an #if arm, the then-branch block the arm's last statement (no `;`); main read the group as the then-branch, C3 reads the block
codeunit 50100 P
{
    procedure T()
    var
        A: Integer;
        C: Boolean;
    begin
#if X
        A := 1;
        if C then
#if Y
#endif
        begin
            A := 2;
        end
#endif
    end;
}
