// B7a Task 10 witness (GAP): family attribute-arguments, base placement one-elem, 3 cells; representative occ:attribute_argument_list:1.0.0@attribute_arguments#one-elem
// Fixture strict_conditional_attribute_args_test.txt#strict attribute arguments MIXED: the whole argument list in the arms of one group (one-elem)#0
// expect: !X reject(AL0238)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:attribute_argument_list:1.0.0@attribute_arguments#one-elem in tools/b7_audit/evidence.jsonl.gz
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
        Ok: Boolean;
        L: List of [Integer];
        Arr: array[3] of Integer;
        Arr2: array[2, 2] of Integer;
        Recs: array[2] of Record T;
    begin
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;

    [IntegrationEvent(
#if X
false , false
#else
false
#endif
)]
    procedure Z()
    begin
    end;
}
