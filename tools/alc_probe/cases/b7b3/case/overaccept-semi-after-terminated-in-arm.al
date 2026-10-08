// B7b-3 Task 6 fix round 1 probe case/overaccept-semi-after-terminated-in-arm: invalid in every configuration; the grammar over-accepts it
// Fixture b7b3_case_separator_negative_test.txt#B7b-3 case known over-acceptance: every arm holds a terminated branch then `;` (invalid in every configuration, alc AL0104,AL0224; classified over-acceptance, deferred-work item 44 precedent)#0
// expect: * reject(AL0104,AL0224)
// source: B7b-3 Task 6 fix round 1, 2026-10-08
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
        1: A;
        ;
#else
        1: A;
        ;
#endif
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
