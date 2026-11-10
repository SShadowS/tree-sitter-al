// B7b-1e (deferred item 46): #if groups inside the member list of an Option TYPE at each host that takes a type: a variable (separator before the member, an `#elif` arm, blank slots in an arm, quoted and keyword members), a parameter followed by another parameter, a return type before `begin`, an interface procedure's return type, and a list wholly inside one arm (the other configuration leaves a bare `Option`). alc accepts every configuration.
// expect: * accept
// source: B7b-1e probe, measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        V1: Option A
#if X
            , B
#elif Y
            , C
#else
            , D
#endif
            ;
        V2: Option ,
#if X
            A,,
#endif
            ,B,;
        V3: Option
#if X
            A, B
#endif
            ;
        V4: Option "A B", Local
#if X
            , Internal, "B C"
#endif
            , Public;

    procedure F(Q: Option A
#if X
        , B
#endif
        ; R: Integer)
    begin
    end;

    procedure G(): Option A
#if X
        , B
#endif
    begin
    end;
}

interface I50101
{
    procedure H(): Option A
#if X
        , B
#endif
}
