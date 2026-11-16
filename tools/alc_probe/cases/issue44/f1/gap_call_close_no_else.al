// The closing group without `#else`: only the configuration that takes the arm closes the call.
// Fixture issue44_f1_gap_test.txt#Issue 44 F1 gap: no else arm, one configuration has no closing paren#0
// expect: * reject(AL0104,AL0301)
// expect: A accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F1)
codeunit 50100 T
{
    procedure P1()
    begin
        V(1,
#if A
          1.0);
#endif
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
