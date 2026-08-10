codeunit 50100 "Selftest Runner"
{
    trigger OnRun()
    begin
        DoWork(1);
    end;

    local procedure DoWork(Value: Integer): Boolean
    var
        Total: Integer;
    begin
        Total := Value * 2;
        if Total > 0 then
            exit(true);
        exit(false);
    end;
}
