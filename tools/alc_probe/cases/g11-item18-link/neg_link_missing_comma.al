// Negative control: no comma between the links.
// expect: * reject
// source: commit 28c601f control (`A = field(B) B = field(A);` REJECT, AL0104)
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
    layout
    {
        area(Content)
        {
            part(L; Q)
            {
                SubPageLink =
                    A = field(B) B = field(A);
            }
        }
    }
}
