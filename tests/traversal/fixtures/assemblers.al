codeunit 50101 "Assemblers"
{
    Permissions = tabledata Customer = r,
#if CLEAN25
                  tabledata Vendor = r;
#else
                  tabledata Item = r,
                  tabledata Resource = r;
#endif

    procedure First()
    begin
    end;

#if CLEAN25
    procedure Split(A: Integer)
#else
    procedure Split(A: Integer; B: Integer)
#endif
    begin
        Message('x');
    end;

    procedure Tail(X: Integer): Integer
    begin
        X := X
#if CLEAN25
            + 1
#endif
            ;
        if X > 0 then
#if CLEAN25
            if X > 1 then begin
                Message('a');
#endif
                Message('b');
#if CLEAN25
            end;
#endif
#pragma warning disable AL0432
        exit(X);
#pragma warning restore AL0432
    end;

    procedure CaseEnd(K: Integer)
    begin
        case K of
            1:
                Message('one');
            2:
#if CLEAN25
                Message('two');
            end;
            Message('after a');
#else
                Message('deux');
            end;
            Message('after b');
#endif
    end;
}

table 50102 "Relations"
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
#if CLEAN25
                else if (Type = const(Resource)) Resource;
#else
                else if (Type = const(Resource)) "G/L Account";
#endif
        }
        field(2; G; Code[20])
        {
            DataClassification =
#if CLEAN25
                CustomerContent;
#else
                SystemMetadata;
#endif
        }
    }
}
