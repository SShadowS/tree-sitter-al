// A group around `local`, around `protected`, and a group choosing between two modifiers,
// with `#else` and with `#elif`. In a table: `protected` in a codeunit is the semantic AL0676.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
table 50100 T
{
    fields
    {
        field(1; K; Code[10]) { }
    }

#if A
    local
#endif
    procedure P1()
    begin
    end;

#if A
    protected
#endif
    procedure P2()
    begin
    end;

#if A
    internal
#else
    local
#endif
    procedure P3()
    begin
    end;

#if A
    internal
#elif B
    protected
#endif
    procedure P4(): Integer
    begin
    end;
}
