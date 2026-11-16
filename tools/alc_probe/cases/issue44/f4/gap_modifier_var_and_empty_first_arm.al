// NOT COVERED by the F4 design: a group around a var section's `protected`, and a group
// whose `#if` arm is empty (`#if A #else internal #endif`).
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }

#if A
#else
    internal
#endif
    procedure P1()
    begin
    end;

#if A
    protected
#endif
    var
        G: Integer;
}
