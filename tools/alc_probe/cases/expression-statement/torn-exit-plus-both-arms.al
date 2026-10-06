// B6 (_expression_statement narrowing): torn exit plus, an invalid fragment in every arm
// Fixture expression_statement_negative_test.txt#B6 negative: exit value torn by an arithmetic %23if arm in every branch#0
// source: B6 task 7 fix round 1, 2026-10-06; the both-arms form of torn-exit-plus.al
// expect: A reject(AL0104,AL0111)
// expect: !A reject(AL0104,AL0111)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure Main(): Integer
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        exit(1)
#if A
        + 2
#else
        + 3
#endif
        ;
    end;
}
