table 50100 "Selftest Customer"
{
    Caption = 'Selftest Customer';
    DataClassification = CustomerContent;

    fields
    {
        field(1; "No."; Code[20])
        {
            Caption = 'No.';
            NotBlank = true;
        }
        field(2; Name; Text[100])
        {
            Caption = 'Name';
        }
    }

    keys
    {
        key(PK; "No.")
        {
            Clustered = true;
        }
    }
}
