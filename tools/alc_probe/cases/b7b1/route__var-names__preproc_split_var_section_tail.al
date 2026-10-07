// B7b-1 Task 2 route cardinality (spec 4.2): route var-names / preproc_split_var_section_tail; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:variable_declaration:2.0.1.0.0@preproc_split_var_section_tail#empty-list.
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X reject(AL0104,AL0107,AL0519)
// expect: TPL2 X accept
// source: predicted from tools/b7_audit/evidence.jsonl.gz (B7a), measured by B7b-1 Task 2, 2026-10-07
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
    var
        A0: Integer;
#if TPL2
        A1: Integer;

        
#if X
X1 , X2
#endif
: Integer;

    procedure P2()
    begin
    end;
#endif

    procedure P3()
    begin
    end;
}
