// B7a Task 10 witness (GAP): family option-members, base placement seed:value-runs__b13-optionmembers-comma-free, 1 cells; representative seed:value-runs__b13-optionmembers-comma-free
// Fixture b7_gap_option_members_test.txt#B7a GAP: option-members / seed:value-runs__b13-optionmembers-comma-free (1 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative seed:value-runs__b13-optionmembers-comma-free#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell seed:value-runs__b13-optionmembers-comma-free in tools/b7_audit/evidence.jsonl.gz
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
interface IFoo { procedure Bar(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50107 FooImpl2 implements IFoo { procedure Bar() begin end; }
table 50100 T { fields { field(1; K; Option) {
OptionMembers =
#if X
    A
#endif
#if not X
    B
#endif
;
} } }
