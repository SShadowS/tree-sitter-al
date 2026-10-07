// B7b-1 Task 2 route cardinality (spec 4.2): route implements / enum_declaration; X undefined empties the list interior
// (delimiters kept), X defined is the compiling non-empty control. Source = audit cell occ:implements_clause:2.0.0@enum_declaration#empty-list.
// expect: !X reject(AL0107)
// expect: X accept
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

codeunit 50103 Impl implements IFoo, IBar, IBaz
{
}

enum 50116 E2 implements 
#if X
IFoo , IBar
#endif

{
    DefaultImplementation = IFoo = Impl, IBar = Impl;
    value(0; V0) { }
}
