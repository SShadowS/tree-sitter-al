// B7b-3 final review probe case/semi-group-then-semi
// Fixture item_47_case_empty_group_test.txt#Item 47 shape 4: a bare semicolon after a semicolon group (a sibling empty_statement, alc accepts X=0)#0
// expect: !X accept
// expect: X reject(AL0104,AL0111,AL0224)
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
            ;
#endif
            ;
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
