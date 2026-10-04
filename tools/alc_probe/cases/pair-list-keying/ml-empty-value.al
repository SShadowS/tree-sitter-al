// CaptionML with no value.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * accept
table 50100 T
{
    CaptionML = ;
    fields { field(1; F; Integer) { } }
}
