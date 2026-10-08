// B7b-3 Task 6 probe case/empty-group-then-semi-at-start: a ; after an empty group with no branch before it
// Fixture b7b3_case_separator_negative_test.txt#B7b-3 case negative: an empty group then a semicolon at the start of case_body (no branch owns it)#0
// expect: !X reject(AL0104,AL0111,AL0224)
// expect: X reject(AL0104,AL0111,AL0224)
// source: B7b-3 Task 6, 2026-10-08
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
#if X
#endif
;
1: Bar;
end;
    end;

    procedure Continue()
    begin
    end;

    procedure A()
    begin
    end;

    procedure B()
    begin
    end;

    procedure Z()
    begin
    end;

    procedure X()
    begin
    end;

    procedure Y()
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
