// expect: * accept
// source: docs/bc29-parse-gaps.md family E (ACCEPT in both configs), commit 42aaf7b
table 50100 T
{
    fields { field(1; A; Integer) { } field(2; B; Integer) { } }
    keys
    {
        key(PK; A) { Clustered = true; }
#if not C28
        key(K2; B) { }
        key(K3; B, A)
#else
        key(K2; B, A)
#endif
        {
        }
    }
}
