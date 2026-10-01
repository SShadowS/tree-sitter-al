// Locked = true is not a Namespaces pair.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0104,AL0219)
xmlport 50100 X
{
    Namespaces = cac = 'urn', Locked = true;
    schema { textelement(R) { } }
}
