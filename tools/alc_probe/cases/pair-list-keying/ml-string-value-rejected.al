// A bare string is not a pair.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0107)
table 50100 T
{
    CaptionML = 'abc';
    fields { field(1; F; Integer) { } }
}
