// Namespaces with no value.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * accept
xmlport 50100 X
{
    Namespaces = ;
    schema { textelement(R) { } }
}
