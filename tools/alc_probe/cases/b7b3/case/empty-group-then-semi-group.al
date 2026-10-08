// B7b-3 final review probe case/empty-group-then-semi-group
// Fixture b7b3_case_separator_negative_test.txt#B7b-3 case known gap: an empty group then a semicolon group after a branch body is read as the next branch's pattern group (alc accepts Y=1; final review M1 b20)#0
// expect: !Y reject(AL0111)
// expect: Y accept
// source: B7b-3 final review (2026-10-08), adversarial input; verdicts measured with tools.alc_probe
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
codeunit 50101 P
{
    procedure Q(): Integer
    var
        R: Record T;
        I: Integer;
        C: Boolean;
        Ok: Boolean;
    begin
        case I of
            1: Bar
#if X
#endif
#if Y
            ;
#endif
            2: Baz;
        end;
    end;

    procedure Continue()
    begin
    end;

    procedure Bar()
    begin
    end;

    procedure Baz()
    begin
    end;

    procedure Order()
    begin
    end;

    procedure Table()
    begin
    end;

    procedure "My Proc"()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
