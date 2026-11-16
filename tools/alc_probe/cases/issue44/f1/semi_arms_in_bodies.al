// Every arm carries the statement's `;` and the call is the body of then / else / while / for / foreach / with /
// a case branch, nested, through an else-if chain, an assignment as a then-branch; a `;` after `#endif` is an
// empty statement; Q7: a directive-only group before the body (item 67's decoration). Covered: _semi_statement (grammar.js), test/corpus/issue44_f1_paren_close_test.txt.
// expect: * accept
// source: reviewer probe rv44f1 bodies/semi_arms_in_bodies.al (Q1-Q4), extended; recorded 2026-11-15, alc 18.0.41
codeunit 50100 T
{
    procedure Q1(C: Boolean)
    begin
        if C then
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        V(1, 3.0);
    end;

    procedure Q2(C: Boolean)
    begin
        if C then
            V(1, 3.0)
        else
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        V(1, 3.0);
    end;

    procedure Q3(C: Boolean)
    var
        I: Integer;
    begin
        while C do
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        for I := 1 to 2 do
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
    end;

    procedure Q4(X: Integer)
    begin
        case X of
            1:
                V(1,
#if A
                  1.0);
#else
                  2.0);
#endif
            2:
                V(1, 3.0);
        end;
    end;

    procedure Q5(C: Boolean)
    var
        I: Integer;
        L: List of [Integer];
    begin
        while C do
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
            ;
        if C then
            while C do
                for I := 1 to 2 do
                    V(1
#if A
                      , 1.0);
#else
                      , 2.0);
#endif
        if C then
            V(1, 1.0)
        else
            if not C then
                V(1, 1.0)
            else
                V(1,
#if A
                  1.0);
#else
                  2.0);
#endif
        foreach I in L do
            with L do
                V(1,
#if A
                  1.0);
#else
                  2.0);
#endif
        if C then
            I := F(1,
#if A
              1.0);
#else
              2.0);
#endif
    end;

    procedure Q6(X: Integer)
    begin
        case X of
            2:
                if X > 1 then
                    V(1,
#if A
                      1.0);
#else
                      2.0);
#endif
            else
                V(1, 3.0);
        end;
    end;

    procedure Q7(C: Boolean; X: Integer)
    begin
        while C do
#if B
#endif
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        if C then
#if B
#endif
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        if C then
            V(1, 3.0)
        else
#if B
#endif
            V(1,
#if A
              1.0);
#else
              2.0);
#endif
        case X of
            1:
#if B
#endif
                V(1,
#if A
                  1.0);
#else
                  2.0);
#endif
        end;
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;

    procedure F(I: Integer; D: Decimal): Integer
    begin
    end;
}
