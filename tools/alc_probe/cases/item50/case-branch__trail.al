// Deferred item 50 (fixed): the former B7a GAP witness of case-branch / trail, representative occ:preproc_split_case_end_branch:1.0@preproc_split_case_statement_end#trail; alc accepts every configuration
// Now parsed: the same shape is the positive case test/corpus/item_50_split_case_end_group_test.txt#Item 50: split case end branch, trail, parenthesized call
// expect: * accept
// source: recorded by B7a, re-read by B7b-3 Task 10, 2026-10-08: the alc split verdicts of cell occ:preproc_split_case_end_branch:1.0@preproc_split_case_statement_end#trail in tools/b7_audit/evidence.jsonl.gz
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
case I of
1:
Bar();
2:
#if TPL

Bar()
#if X
;
#endif

end;
I := 1;
#else
begin
Bar();
end
end;
I := 2;
#endif
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
