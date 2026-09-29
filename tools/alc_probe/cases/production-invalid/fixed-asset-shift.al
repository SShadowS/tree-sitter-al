// Source bcapps-29.0:src/Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al
// source: milestone-2 results doc, "Resolve sweep" (four-way probe); recorded by A4, 2026-09-29
// expect: * accept
// expect: CLEANSCHEMA26 reject(AL0104,AL0162,AL0198)
// A field opened inside `#if not CLEANSCHEMA26`, its trigger and `}` after `#endif`.
// With CLEANSCHEMA26 defined, the header and `{` go and the `}` closes `fields` early.
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not CLEANSCHEMA26
        field(13; B; Code[10])
        {
            Caption = 'B';
            ObsoleteReason = 'x';
            ObsoleteState = Removed;
#pragma warning disable AS0072
            ObsoleteTag = '26.0';
#pragma warning restore AS0072
#endif
            trigger OnValidate()
            begin
                P();
            end;
        }
        field(14; C; Date) { }
    }
    procedure P()
    begin
    end;
}
