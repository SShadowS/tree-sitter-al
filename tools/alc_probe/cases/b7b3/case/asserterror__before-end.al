// B7b-3 Phase 0 probe case/asserterror__before-end
// Fixture b7b3_case_separator_test.txt#B7b-3 case separators: asserterror body, two semicolon groups before end (Phase 0 asserterror__before-end)#0
// expect: !S1 !S2 accept
// expect: !S1 S2 accept
// expect: S1 !S2 accept
// expect: S1 S2 reject(AL0104,AL0224)
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
                asserterror Bar()
#if S1
;
#endif
#if S2
;
#endif
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
