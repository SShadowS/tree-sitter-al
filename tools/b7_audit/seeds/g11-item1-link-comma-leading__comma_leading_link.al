// host: link_value_list
// valid: *
// seed-source: tools/alc_probe/cases/g11-item1-link-comma-leading/comma_leading_link.al (verdicts measured by alc, as recorded in its expect lines)
// source: docs/deferred-work.md item 1 (link reproducer)
// The parser still ERRORs on this shape (deferred-work item 1); alc accepts it.
// expect: * accept
// source: docs/deferred-work.md item 1 (link_value_list, comma-leading shape), commit 44fd67c: alc accepts all four configurations (G11 review probe)
table 50101 Q
{
    fields { field(1; B; Integer) { } field(2; D; Integer) { } field(3; F; Integer) { } }
}
page 50100 P
{
    SourceTable = T;
    layout
    {
        area(Content)
        {
            part(L; S)
            {
                SubPageLink = B = field(A)
#if X
                    , D = field(C)
#endif
                    , F = field(E);
            }
        }
    }
}
page 50101 S
{
    SourceTable = Q;
    layout { area(Content) { field(B; Rec.B) { } } }
}
table 50100 T
{
    fields { field(1; A; Integer) { } field(2; C; Integer) { } field(3; E; Integer) { } }
}
