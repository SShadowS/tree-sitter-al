// B7a Task 10 witness (GAP): family namespace-using, base placement sep-only, 12 cells; representative occ:namespace_declaration:2@preproc_conditional_object#sep-only
// Fixture b7_gap_namespace_using_test.txt#B7a GAP: namespace-using / sep-only (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:namespace_declaration:2@preproc_conditional_object%23sep-only#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:namespace_declaration:2@preproc_conditional_object#sep-only in tools/b7_audit/evidence.jsonl.gz
#if TPL

namespace Foo.Bar
#if X
;
#else
;
#endif

#else
namespace Foo.Bar;
#endif

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
}
