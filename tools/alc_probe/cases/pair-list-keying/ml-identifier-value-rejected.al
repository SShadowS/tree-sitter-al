// Pair value must be a string literal.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0104,AL0219)
table 50100 T
{
    CaptionML = ENU=Foo;
    fields { field(1; F; Integer) { } }
}
