// Keyword as a middle segment, a table under a namespace.
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.1
// expect: * accept
namespace Acme;
table 50210 "DataseT" { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = Acme.DataseT."No.";
        }
        field(2; F2; Integer) { }
        field(3; "Currency Code"; Code[10]) { }
        field(4; Flag; Boolean) { }
        field(5; Flag2; Boolean) { }
    }
}
