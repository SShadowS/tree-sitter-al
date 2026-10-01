// Semantic rejection (InvalidLanguageId): still parses as a pair.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0160)
table 50100 T
{
    CaptionML = ENU='a', Locked='x';
    fields { field(1; F; Integer) { } }
}
