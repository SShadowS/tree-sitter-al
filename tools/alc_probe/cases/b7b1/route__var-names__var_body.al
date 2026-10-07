// B7b-1 Task 2 route cardinality (spec 4.2): route var-names / var_body; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:variable_declaration:2.0.1.0.0@var_body#empty-list.
// expect: !X reject(AL0104,AL0198)
// expect: X accept
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
        
#if X
X1 , X2
#endif
: Integer;
}
