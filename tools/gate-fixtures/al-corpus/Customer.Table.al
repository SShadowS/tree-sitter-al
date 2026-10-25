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
        // validate --full Step 6c refuses a corpus with no TableRelation site
        field(3; "Parent No."; Code[20])
        {
            Caption = 'Parent No.';
            TableRelation = "Selftest Customer"."No." where(Name = const('Parent'));
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
