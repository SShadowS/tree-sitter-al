codeunit 9999999 "Sample Table Field Array Management"
{
    // Odd array number is a Table No.
    // Even array number is a Field No.

    trigger OnRun()
    begin
    end;

    procedure GetTableFieldCaption(InputArray: Text[1024]): Text[1024]
    var
        FieldArray: array[20] of Integer;
    begin
        TextToArray(FieldArray, InputArray);
        EXIT(GetFieldArrayCaption(FieldArray));
    end;

    procedure GetFieldArrayCaption(FieldArray: array[20] of Integer) ReturnValue: Text[1024]
    var
        i: Integer;
    begin
        FOR i := 1 TO ARRAYLEN(FieldArray) DO BEGIN
            IF FieldArray[i] = 0 THEN
                EXIT;

            IF ReturnValue = '' THEN
                ReturnValue := GetFieldCaption(FieldArray[i], FieldArray[i + 1])
            ELSE
                ReturnValue += ' -> ' + GetTableAndFieldCaption(FieldArray[i], FieldArray[i + 1]);
            i += 1;
        END;
    end;

    procedure GetFieldArrayFieldCaption(InputArray: Text) ReturnValue: Text
    var
        RecField: Record "Field";
    begin
        IF GetFieldRecord(RecField, InputArray) THEN
            ReturnValue := RecField."Field Caption";
    end;

    procedure GetTableAndFieldCaption(TableNo: Integer; FieldNo: Integer): Text[1024]
    begin
        IF (TableNo > 0) AND (FieldNo > 0) THEN
            EXIT(STRSUBSTNO('%1 - %2', GetTableCaption(TableNo), GetFieldCaption(TableNo, FieldNo)));
    end;

    procedure GetTableCaption(TableNo: Integer): Text[1024]
    var
        AllObjects: Record AllObjWithCaption;
    begin
        IF AllObjects.GET(AllObjects."Object Type"::Table, TableNo) THEN BEGIN
            EXIT(AllObjects."Object Caption");
        END;
    end;

    procedure GetFieldCaption(TableNo: Integer; FieldNo: Integer): Text[1024]
    var
        RecField: Record "Field";
    begin
        IF RecField.GET(TableNo, FieldNo) THEN
            EXIT(RecField."Field Caption");
    end;

    procedure GetFieldRecord(var RecField: Record "Field"; InputArray: Text): Boolean
    var
        FieldArray: array[20] of Integer;
        i: Integer;
    begin
        IF InputArray = '' THEN
            EXIT(FALSE);
        TextToArray(FieldArray, InputArray);
        FOR i := 3 TO ARRAYLEN(FieldArray) DO BEGIN
            IF FieldArray[i] = 0 THEN
                IF RecField.GET(FieldArray[i - 2], FieldArray[i - 1]) THEN
                    EXIT(TRUE);
            i += 1;
        END;
    end;

    procedure FindFieldRelationValue(var FilterRec: RecordRef; var TempBlob: Record "Sample Temp Blob"; InputArray: Text; FormatString: Text) ReturnText: Text
    var
        RecRef: RecordRef;
        FRef: FieldRef;
        FRef2: FieldRef;
        KRef: KeyRef;
        FilterValue: Text[1024];
        FieldArray: array[20] of Integer;
        i: Integer;
    begin
        IF InputArray = '' THEN
            EXIT;
        TextToArray(FieldArray, InputArray);
        FRef := FilterRec.FIELD(FieldArray[2]);

        IF GetBlobOrMedia(TempBlob, FRef) THEN
            EXIT('Sample::Picture');

        IF FORMAT(FRef.CLASS) = 'FlowField' THEN
            FRef.CALCFIELD;
        FilterValue := FORMAT(FRef.VALUE);

        IF (FieldArray[3] = 0) OR (FilterValue = '') THEN
            EXIT(UseFormatString(FRef.VALUE, FormatString))
        ELSE BEGIN
            RecRef.CLOSE;
            FOR i := 3 TO ARRAYLEN(FieldArray) DO BEGIN // Jumps with 2 (3,5,7 etc.)
                RecRef.OPEN(FieldArray[i]);
                i += 1; // Next is Field No.

                // Specific table checks
                IF (FilterRec.NUMBER IN [DATABASE::"Sales Header", DATABASE::"Sales Shipment Header", DATABASE::"Sales Invoice Header", DATABASE::"Sales Cr.Memo Header", DATABASE::"Return Receipt Header",
                    DATABASE::"Purchase Header", DATABASE::"Purch. Rcpt. Header", DATABASE::"Purch. Inv. Header", DATABASE::"Purch. Cr. Memo Hdr.", DATABASE::"Return Shipment Header"]) AND
                   (RecRef.NUMBER = DATABASE::"Ship-to Address")
                THEN BEGIN
                    KRef := RecRef.KEYINDEX(1);

                    CASE FilterRec.NUMBER OF
                        DATABASE::"Sales Header", DATABASE::"Sales Shipment Header", DATABASE::"Sales Invoice Header", DATABASE::"Sales Cr.Memo Header", DATABASE::"Return Receipt Header":
                            FRef2 := FilterRec.FIELD(2); // Sell-to Customer No. - Sales Tables
                        DATABASE::"Purchase Header", DATABASE::"Purch. Rcpt. Header", DATABASE::"Purch. Inv. Header", DATABASE::"Purch. Cr. Memo Hdr.", DATABASE::"Return Shipment Header":
                            FRef2 := FilterRec.FIELD(72); // Sell-to Customer No. - Purchase Tables
                    END;
                    FRef := KRef.FIELDINDEX(1);
                    FRef.SETFILTER(FORMAT(FRef2.VALUE));
                    FRef := KRef.FIELDINDEX(2);
                    IF STRLEN(FilterValue) > FRef.LENGTH THEN
                        ERROR('The value %1 is longer than the max value %2\Trying to set filter on field %3 (%4) table %5 (%6)\From Table no.: %7 field no. %8',
                          FilterValue, FRef.LENGTH, FRef.NAME, FRef.NUMBER, RecRef.NAME, RecRef.NUMBER, FieldArray[i - 3], FieldArray[i - 2]);
                    FRef.SETRANGE(FilterValue);
                END ELSE BEGIN
                    KRef := RecRef.KEYINDEX(1);
                    IF KRef.FIELDCOUNT > 1 THEN
                        ERROR('The Table %1 has more than one field in Primary Key.', RecRef.CAPTION);
                    FRef := KRef.FIELDINDEX(1);
                    IF STRLEN(FilterValue) > FRef.LENGTH THEN
                        ERROR('The value %1 is longer than the max value %2\Trying to set filter on field %3 (%4) table %5 (%6)\From Table no.: %7 field no. %8',
                          FilterValue, FRef.LENGTH, FRef.NAME, FRef.NUMBER, RecRef.NAME, RecRef.NUMBER, FieldArray[i - 3], FieldArray[i - 2]);
                    FRef.SETRANGE(FilterValue);
                END;
                IF NOT RecRef.FINDFIRST THEN
                    EXIT('');
                FRef := RecRef.FIELD(FieldArray[i]);

                IF GetBlobOrMedia(TempBlob, FRef) THEN
                    EXIT('Sample::Picture');

                IF FORMAT(FRef.CLASS) = 'FlowField' THEN
                    FRef.CALCFIELD;

                IF FieldArray[i + 1] = 0 THEN
                    EXIT(UseFormatString(FRef.VALUE, FormatString));

                FilterValue := FORMAT(FRef.VALUE);
                RecRef.CLOSE;
                IF FilterValue = '' THEN
                    EXIT;
            END;
        END;
    end;

    local procedure GetBlobOrMedia(var TempBlob: Record "Sample Temp Blob"; var FRef: FieldRef): Boolean
    var
        MediaSet: Record "Tenant Media Set";
        Media: Record "Tenant Media";
    begin
        CASE FORMAT(FRef.TYPE) OF
            'BLOB':
                BEGIN
                    FRef.CALCFIELD;
                    TempBlob.Blob := FRef.VALUE;
                    EXIT(TRUE);
                END;
            'Media':
                BEGIN
                    Media.GET(FORMAT(FRef.VALUE));
                    Media.CALCFIELDS(Content);
                    TempBlob.Blob := Media.Content;
                    EXIT(TRUE);
                END;
            'MediaSet':
                BEGIN
                    MediaSet.SETRANGE(ID, FORMAT(FRef.VALUE));
                    IF MediaSet.FINDFIRST THEN BEGIN
                        Media.GET(MediaSet."Media ID".MEDIAID);
                        Media.CALCFIELDS(Content);
                        TempBlob.Blob := Media.Content;
                        EXIT(TRUE);
                    END;
                END;
        END;
    end;

    procedure TextToArray(var NewFieldArray: array[20] of Integer; InputArray: Text[1024])
    var
        i: Integer;
    begin
        CLEAR(NewFieldArray);
        IF InputArray = '' THEN
            EXIT;

        WHILE STRPOS(InputArray, ',') > 0 DO BEGIN
            i += 1;
            EVALUATE(NewFieldArray[i], COPYSTR(InputArray, 1, STRPOS(InputArray, ',') - 1));
            InputArray := COPYSTR(InputArray, STRPOS(InputArray, ',') + 1);
        END;
        i += 1;
        EVALUATE(NewFieldArray[i], InputArray);
    end;

    procedure ArrayToText(FieldArray: array[20] of Integer) ReturnValue: Text[1024]
    var
        i: Integer;
    begin
        FOR i := 1 TO ARRAYLEN(FieldArray) DO BEGIN
            IF FieldArray[i] = 0 THEN
                EXIT;

            IF ReturnValue = '' THEN
                ReturnValue := STRSUBSTNO('%1,%2', FieldArray[i], FieldArray[i + 1])
            ELSE
                ReturnValue += STRSUBSTNO(',%1,%2', FieldArray[i], FieldArray[i + 1]);

            i += 1; // For loop only runs through odd numbers
        END;
    end;

    procedure UseFormatString(Value: Variant; FormatString: Text) ReturnText: Text
    var
        IsBlankZero: Boolean;
    begin
        IF STRPOS(FormatString, '<BlankZero>') > 0 THEN BEGIN
            IsBlankZero := TRUE;
            FormatString := DELSTR(FormatString, STRPOS(FormatString, '<BlankZero>'), 11);
        END;
        IF FormatString = '' THEN
            ReturnText := FORMAT(Value)
        ELSE
            ReturnText := FORMAT(Value, 0, FormatString);
        IF (DELCHR(ReturnText, '=', '0.,') = '') AND IsBlankZero THEN
            ReturnText := '';
    end;
}
