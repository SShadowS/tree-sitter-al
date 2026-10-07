// B7b-1 Task 2 route cardinality (spec 4.2): route implements / preproc_split_declaration; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:implements_clause:2.0.0@preproc_split_declaration#empty-list.
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0107)
// expect: TPL X accept
// source: predicted from tools/b7_audit/evidence.jsonl.gz (B7a), measured by B7b-1 Task 2, 2026-10-07
interface IFoo
{
}

interface IBar
{
}

interface IBaz
{
}

#if TPL
codeunit 50111 C2 implements 
#if X
IFoo , IBar
#endif

#else
codeunit 50111 C2 implements IFoo
#endif
{
}
