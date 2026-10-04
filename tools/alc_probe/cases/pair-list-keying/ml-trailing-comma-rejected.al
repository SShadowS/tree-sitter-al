// ListCannotEndWithSeparator.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0301)
table 50100 T
{
    CaptionML = ENU='a',;
    fields { field(1; F; Integer) { } }
}
