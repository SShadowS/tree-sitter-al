// B5 host case: pageextension modify, flat. alc rejects it: AL0246 "The property
// 'TableRelation' cannot be customized. This property is read-only in the current context."
// So this host gets no fixture in test/corpus/table_relation_keying_test.txt (spec 5.2).
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md section 5.2
// expect: * reject(AL0246)
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50102 "G/L Account" { fields { field(1; "No."; Code[20]) { } } }
table 50103 Vendor { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; F; Code[20]) { }
        field(2; F2; Integer) { }
    }
}
page 50100 P
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
            field(F; Rec.F) { }
        }
    }
}
pageextension 50120 PE extends P
{
    layout
    {
        modify(F)
        {
            TableRelation = if (F2 = const(1)) Customer else Vendor where("No." = const('A'));
        }
    }
}
