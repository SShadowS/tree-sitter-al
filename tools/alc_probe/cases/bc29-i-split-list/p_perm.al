// expect: * accept
// source: docs/bc29-parse-gaps.md family I (ACCEPT in both configs), commit 32461af
table 50100 TA { fields { field(1; A; Integer) { } } }
table 50101 TB { fields { field(1; A; Integer) { } } }
table 50102 TC { fields { field(1; A; Integer) { } } }
permissionset 50100 PS
{
    Access = Public;
#if not C29
    Permissions = tabledata TA = RIMD,
                  tabledata TB = RIMD,
#else
    Permissions = tabledata TB = RIMD,
#endif
                  tabledata TC = RIMD;
}
