// Valid only with CLEANSCHEMA26 undefined (the FixedAssetShift shape).
// expect: * accept
// expect: CLEANSCHEMA26 reject
// source: docs/bc29-parse-gaps.md family D (undefined ACCEPT, CLEANSCHEMA26 REJECT with AL0104, AL0162), commit 5b809bc
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
