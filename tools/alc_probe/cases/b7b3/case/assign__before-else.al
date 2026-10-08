// B7b-3 Phase 0 probe case/assign__before-else
// Fixture b7b3_case_separator_test.txt#B7b-3 case separators: assign body, two semicolon groups before the case else (Phase 0 assign__before-else)#0
// expect: !S1 !S2 accept
// expect: !S1 S2 accept
// expect: S1 !S2 accept
// expect: S1 S2 reject(AL0104,AL0110,AL0224)
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
            1:
                Ok := true
#if S1
;
#endif
#if S2
;
#endif
        else
            Ok := false;
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
