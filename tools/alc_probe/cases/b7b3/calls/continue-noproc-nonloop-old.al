// B7b-3 Phase 0 probe calls/continue-noproc-nonloop-old
// expect: * reject(AL0118)
// runtime: 12.0 13.0 14.0
// source: B7b-3 Phase 0 fix round 1, 2026-10-08
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
    procedure Q()
    var
        C: Boolean;
    begin
        continue;
    end;
}
