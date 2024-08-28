table 6175306 "CDO File Download Document"
{
    Caption = 'File Download Document';
    PasteIsValid = false;
    LookupPageID = "CDO File Download Queue";
    DrillDownPageID = "CDO File Download Queue";

    fields
    {
        field(1; "Entry no."; Integer)
        {
            Caption = 'Entry no.';
            DataClassification = CustomerContent;
        }
        field(2; "Path"; Text[250])
        {
            Caption = 'Path';
            DataClassification = CustomerContent;
        }
        field(3; "Filename"; Text[250])
        {
            Caption = 'Filename';
            DataClassification = CustomerContent;
        }
        field(4; "Filedata"; BLOB)
        {
            Caption = 'Filedata';
            DataClassification = CustomerContent;
        }
        field(5; "Download started"; DateTime)
        {
            Caption = 'Download started';
            DataClassification = CustomerContent;
        }
        field(6; "Error message"; Text[250])
        {
            Caption = 'Error message';
            DataClassification = CustomerContent;
        }
        field(7; "No. of errors"; Integer)
        {
            Caption = 'No. of errors';
            DataClassification = CustomerContent;
        }
    }
    keys
    {
        key(Key1; "Entry no.")
        {
        }

    }
    trigger OnInsert()
    var
        DOFileDownloadDocument: Record "CDO File Download Document";
    begin
        if DOFileDownloadDocument.FindLast() then
            "Entry no." := DOFileDownloadDocument."Entry no." + 1
        else
            "Entry no." := 1;
    end;

    procedure Create(var DOFile: Record 6175301; DownloadPath: Text);
    begin
        Init();
        Path := DownloadPath;
        Filename := DOFile.Filename;
        Filedata := DOFile."File Blob";
        Insert(true);
    end;

    procedure SetErrorMessage(ErrorMessage: Text);
    begin
        "Error message" := COPYSTR(ErrorMessage, 1, MAXSTRLEN("Error message"));
        "No. of errors" += 1;
        Modify();
    end;

    procedure DownloadFile();
    var
        DOFile: Record "CDO File";
    begin
        CALCFIELDS(Filedata);
        if Filedata.HASVALUE then begin
            DOFile.SetFilename(Filename);
            DOFile."File Blob" := Filedata;
            DOFile.ShowSaveFile(FALSE);
        end;
    end;

    procedure RestartDownload();
    begin
        "Error message" := '';
        "Download started" := 0DT;
        Modify();
    end;

}

