table 9999999 "Sample E-Mail Recipient"
{
    Caption = 'Sample E-Mail Recipient';
    DrillDownPageId = "Sample E-Mail Recipients";

    fields
    {
        field(7; "Recipient No."; Code[20])
        {
            TableRelation = IF ("Company No." = FILTER(<> '')) "Recipient" WHERE("No." = FIELD("Company No.")) ELSE
            IF ("Company No." = CONST()) "Recipient";
            Caption = 'Recipient No.';
            DataClassification = CustomerContent;
            trigger OnValidate()
            begin
                CALCFIELDS("Recipient Name", "Recipient E-Mail");
            end;

        }
        field(8; "Recipient Name"; Text[100])
        {
            FieldClass = "FlowField";
            CalcFormula = Lookup(Recipient.Name WHERE("No." = FIELD("Recipient No.")));
            Caption = 'Recipient Name';
            Editable = false;
        }
        field(10; "E-Mail Address"; Text[250])
        {
            ExtendedDatatype = EMail;
            Caption = 'E-Mail Address';
            DataClassification = CustomerContent;
            trigger OnValidate()
            var
                EmailManagement: Codeunit "Sample E-Mail Management";
            begin
                "E-Mail Address" := DELCHR("E-Mail Address", '<>');
                EmailManagement.CheckValidEmailAddress("E-Mail Address");
            end;
        }
        field(15; "Recipient E-Mail"; Text[250])
        {
            FieldClass = "FlowField";
            CalcFormula = Lookup(Recipient."E-Mail Address" WHERE("No." = FIELD("Recipient No.")));
            ExtendedDatatype = EMail;
            Caption = 'Recipient E-Mail';
            Editable = false;
        }

    }
    keys
    {
        key(Key1; "Entry No.")
        {
        }
    }
    trigger OnInsert()
    begin
        SetCompanyNo;
    end;


    procedure SetCompanyNo();
    var
        Rec: Record Recipient;
        BusinessRelation: Record "Recipient Business Relation";
    begin
        CASE Table OF
            Table::Customer:
                begin
                    BusinessRelation.SETRANGE("Link to Table", BusinessRelation."Link to Table"::Customer);
                    BusinessRelation.SETRANGE("No.", "No.");
                    IF BusinessRelation.FINDFIRST THEN
                        "Company No." := BusinessRelation."Recipient No.";
                end;
            Table::Vendor:
                begin
                    BusinessRelation.SETRANGE("Link to Table", BusinessRelation."Link to Table"::Vendor);
                    BusinessRelation.SETRANGE("No.", "No.");
                    IF BusinessRelation.FINDFIRST THEN
                        "Company No." := BusinessRelation."Recipient No.";
                end;
            Table::Recipient:
                begin
                    IF Rec.GET("No.") THEN
                        "Company No." := Rec."Company No.";
                end;
        end;
    end;

    procedure GetEmailAddress(): Text[80];
    begin
        CASE "E-Mail Type" OF
            "E-Mail Type"::Contact:
                begin
                    CALCFIELDS("Recipient E-Mail");
                    EXIT("Recipient E-Mail");
                end;
            "E-Mail Type"::"E-Mail address":
                EXIT("E-Mail Address");
        end;
    end;

    procedure ReportID(): Integer;
    var
        TemplateHeader: Record "Sample E-Mail Template Header";
    begin
        IF "Document Type" = "Document Type"::"E-Mail Template" THEN
            IF TemplateHeader.GET("Document Code") THEN
                EXIT(TemplateHeader."Report-ID");
    end;

    procedure ReportName(): Text;
    var
        AllObjects: Record 2000000038;
    begin
        IF AllObjects.GET(AllObjects."Object Type"::Report, ReportID) THEN
            EXIT(AllObjects."Object Name");
    end;

    procedure GetTemplate();
    var
        EmailRecipient: Record "Sample E-Mail Recipient";
        EmailRecipientTemplate: Record "Sample E-Mail Recipient Template";
    begin
        IF (GETFILTER(Table) = '') OR (GETFILTER("No.") = '') THEN
            EXIT;
        COPYFILTER(Table, EmailRecipientTemplate.Table);
        IF EmailRecipientTemplate.FINDSET THEN
            REPEAT
                EmailRecipient.TRANSFERFIELDS(EmailRecipientTemplate);
                EmailRecipient."No." := GETFILTER("No.");
                EmailRecipient."Entry No." := 0;
                EmailRecipient.SETRANGE(Table, EmailRecipient.Table);
                EmailRecipient.SETRANGE("No.", EmailRecipient."No.");
                EmailRecipient.SETRANGE("Document Type", EmailRecipient."Document Type");
                EmailRecipient.SETRANGE("Document Code", EmailRecipient."Document Code");
                EmailRecipient.SETRANGE("Recipient Type", EmailRecipient."Recipient Type");
                EmailRecipient.SETRANGE("E-Mail Type", EmailRecipient."E-Mail Type");
                IF EmailRecipient.ISEMPTY THEN BEGIN
                    EmailRecipient.SetCompanyNo;
                    EmailRecipient.INSERT;
                end;
            UNTIL EmailRecipientTemplate.NEXT = 0;
    end;

    procedure DeleteTemplateRecipients();
    var
        EmailRecipient: Record "Sample E-Mail Recipient";
        EmailRecipientTemplate: Record "Sample E-Mail Recipient Template";
    begin
        COPYFILTER(Table, EmailRecipientTemplate.Table);
        IF EmailRecipientTemplate.FINDSET THEN
            REPEAT
                EmailRecipient.TRANSFERFIELDS(EmailRecipientTemplate);
                EmailRecipient."No." := GETFILTER("No.");
                EmailRecipient.SETRANGE(Table, EmailRecipient.Table);
                EmailRecipient.SETRANGE("No.", EmailRecipient."No.");
                EmailRecipient.SETRANGE("Document Type", EmailRecipient."Document Type");
                EmailRecipient.SETRANGE("Document Code", EmailRecipient."Document Code");
                EmailRecipient.SETRANGE("Recipient Type", EmailRecipient."Recipient Type");
                EmailRecipient.SETRANGE("E-Mail Type", EmailRecipient."E-Mail Type");
                EmailRecipient.SETRANGE("Recipient No.", '');
                EmailRecipient.SETRANGE("E-Mail Address", '');
                EmailRecipient.DELETEALL;
            UNTIL EmailRecipientTemplate.NEXT = 0;
    end;

}
