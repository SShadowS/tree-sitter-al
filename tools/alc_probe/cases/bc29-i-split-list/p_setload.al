// expect: * accept
// source: docs/bc29-parse-gaps.md family I (ACCEPT in both configs), commit 32461af
table 50100 Tb { fields { field(1; A; Integer) { } field(2; B; Integer) { } field(3; C; Integer) { } } }
codeunit 50100 T
{
    procedure P()
    var
        R: Record Tb;
    begin
        R.SetLoadFields(A,
#if not C28
            B,
#endif
            C);
    end;
}
