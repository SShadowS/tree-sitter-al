// Valid only with CLEANSCHEMA26 undefined (the FixedAssetShift shape).
// expect: * accept
// expect: CLEANSCHEMA26 reject(AL0104,AL0162,AL0198)
// source: docs/bc29-parse-gaps.md family D (undefined ACCEPT, CLEANSCHEMA26 REJECT with AL0104, AL0162), commit 5b809bc
// source: AL0198: recorded by A2, 2026-09-29 (the record lists AL0104, AL0162 only)
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not CLEANSCHEMA26
        field(13; B; Code[10])
        {
            ObsoleteState = Removed;
#endif
            trigger OnValidate()
            begin
            end;
        }
        field(14; C; Date) { }
    }
}
