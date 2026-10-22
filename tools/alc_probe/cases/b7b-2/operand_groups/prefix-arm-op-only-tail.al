// B7b-2 Phase C (Task 10): an operator-only nested tail inside a prefix arm, `1 + #if T 3 #if X + #endif 2 + #endif 2`
// Fixture b7b2_operand_group_test.txt#B7b-2 operand group: prefix arm: an operator-only nested tail#0
// expect: !T accept
// expect: T X accept
// expect: T !X reject(AL0104,AL0111)
// source: B7b-2 Phase C (Task 10), 2026-10-21
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer;
    begin
        I := 1 +
#if T
            3
#if X
            +
#endif
            2 +
#endif
            2;
    end;
}
