// host: link_value_list
// valid: *
// seed-source: tools/alc_probe/cases/g11-item18-link/runpagelink_action.al (verdicts measured by alc, as recorded in its expect lines)
// expect: * accept
// source: docs/deferred-work.md item 18 (link list), commit 28c601f: alc four-way ACCEPT
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
        field(2; B; Integer) { }
        field(3; C; Integer) { }
        field(4; D; Integer) { }
    }
}
page 50101 Q
{
    PageType = ListPart;
    SourceTable = T;
    layout { area(Content) { repeater(R) { field(A; Rec.A) { } } } }
}
page 50102 P
{
    PageType = Card;
    SourceTable = T;
    actions
    {
        area(Processing)
        {
            action(Act)
            {
                RunObject = page Q;
                RunPageLink =
#if X
                    A = field(B),
#endif
                    B = field(A);
            }
        }
    }
}
