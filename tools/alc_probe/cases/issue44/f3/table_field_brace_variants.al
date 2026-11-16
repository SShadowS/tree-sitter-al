// Neighbours of the issue's shape. Field 10: a complete field leads an arm. Field 11: a
// nested group chooses the header inside an arm. Field 12: a comment and a pragma inside
// the arms. Field 13: the `{` in one arm only would be invalid in the other configuration,
// so it is not here; instead the header in the arms and the `{` shared (the existing
// preproc_split_table_field shape) as the control.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F3)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
#if A
        field(9; F9; Integer) { }
        field(10; F10; Integer)
        {
#else
        field(10; F10; Code[10])
        {
#endif
            DataClassification = CustomerContent;
        }
#if A
#if B
        field(11; F11; Integer)
        {
#else
        field(11; F11; Decimal)
        {
#endif
#else
        field(11; F11; Code[10])
        {
#endif
            DataClassification = CustomerContent;
        }
#if A
        // a comment
        field(12; F12; Integer)
#pragma warning disable AA0137
        {
#pragma warning restore AA0137
#else
        field(12; F12; Code[10])
        { // trailing
#endif
            DataClassification = CustomerContent;
        }
#if A
        field(13; F13; Integer)
#else
        field(13; F13; Code[10])
#endif
        {
            DataClassification = CustomerContent;
        }
    }
}
