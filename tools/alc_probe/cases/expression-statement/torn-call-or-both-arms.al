// B6 (_expression_statement narrowing): torn call or/and, an invalid fragment in every arm
// Fixture expression_statement_negative_test.txt#B6 negative: call torn by a keyword-operator %23if arm in every branch#0
// source: B6 task 7 fix round 1, 2026-10-06; the both-arms form of torn-call-or.al
// expect: A reject(AL0117)
// expect: !A reject(AL0117)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure Main()
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        Foo()
#if A
        or (2 = 2)
#else
        and (3 = 3)
#endif
        ;
    end;
}
