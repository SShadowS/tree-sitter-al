// B7b-3 Phase 0 probe case/lone-group-after-terminated
// Fixture b7b3_case_separator_test.txt#B7b-3 case separators: lone semicolon group after a terminated branch (Phase 0 lone-group-after-terminated; the X configuration is ;; and rejected)#0
// expect: !X accept
// expect: X reject(AL0104,AL0111,AL0224)
// source: B7b-3 Phase 0, 2026-10-08
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
            1: Bar;
#if X
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
