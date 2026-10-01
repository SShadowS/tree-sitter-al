// Namespaces pair with a quoted (empty) prefix.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * accept
xmlport 50100 X
{
    Namespaces = "" = 'urn';
    schema { textelement(R) { } }
}
