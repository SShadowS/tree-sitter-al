// A group choosing a table field header WITH its `{` inside each arm; the body after #endif.
// Field 10: the issue's shape. Field 11: three arms. Field 12: properties inside the arms
// before the shared ones. Field 13: nothing shared (the `}` right after #endif).
// expect: * accept
// source: gh issue #44 repro 4; recorded 2026-11-15, alc 18.0.41
enum 50100 "My Enum"
{
    value(0; A) { }
}
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
#if V15
        field(10; "Round"; Enum "My Enum")
        {
#else
        field(10; "Round"; Integer)
        {
#endif
            DataClassification = CustomerContent;
        }
#if V15
        field(11; F11; Enum "My Enum")
        {
#elif V14
        field(11; F11; Integer)
        {
#else
        field(11; F11; Code[20])
        {
#endif
            DataClassification = CustomerContent;
        }
#if V15
        field(12; F12; Enum "My Enum")
        {
            Caption = 'a';
#else
        field(12; F12; Integer)
        {
            Caption = 'b';
            MinValue = 0;
#endif
            DataClassification = CustomerContent;

            trigger OnValidate()
            begin
            end;
        }
#if V15
        field(13; F13; Enum "My Enum")
        {
#else
        field(13; F13; Integer)
        {
#endif
        }
        field(14; F14; Integer) { }
    }
}
