// Deferred-work 31/32/34 bundle: chartpart-repeater.
// source: docs/deferred-work.md items 31, 32, 34
// expect: * reject(AL0376)
table 50101 Cust { fields { field(1; "No."; Code[20]) { } field(2; Name; Text[30]) { } field(3; Amount; Decimal) { } field(4; Flag; Boolean) { } field(5; Kind; Option) { OptionMembers = Open,Closed; } field(6; Posted; Date) { } field(7; At; Time) { } field(8; Stamp; DateTime) { } field(9; Big; BigInteger) { } } }
page 50102 CustCard { PageType = Card; SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50103 CustList { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(N; Rec."No.") { } } } } }
page 50100 P { PageType = List; SourceTable = Cust; layout { area(Content) { repeater(R) { chartpart(C; "Sales Chart") { } } } } }
