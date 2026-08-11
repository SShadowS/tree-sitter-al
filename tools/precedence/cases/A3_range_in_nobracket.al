codeunit 50100 Probe
{
    procedure Q(x: Integer)
    begin
    end;

    procedure P()
    var
        i: Integer;
        b: Boolean;
        t: Text;
        arr: array[10] of Boolean;
    begin
        b := 1 in 1 .. 5;
    end;

    procedure BoolFn(): Boolean
    begin
        exit(true);
    end;
}
