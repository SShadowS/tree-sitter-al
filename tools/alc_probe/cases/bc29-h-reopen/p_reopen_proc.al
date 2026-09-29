// expect: * accept
// source: docs/bc29-parse-gaps.md family H (ACCEPT x2), commit 21938f3
codeunit 50100 T
{
    local procedure P()
    begin
        Message('a');
#if not C27
        Message('b');
#else
        Message('c');
    end;

    local procedure Q(): Text
    begin
        exit('');
#endif
    end;
}
