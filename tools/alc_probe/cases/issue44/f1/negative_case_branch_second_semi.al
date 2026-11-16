// A case branch whose body's `;` is in every arm, then a second `;` after `#endif`: `1: V(1, 1.0);;` in every
// configuration. alc rejects it (a case branch takes one statement and one `;`), so the semi_ case branch arm
// takes no `;` of its own and the parser ERRORs on the second.
// expect: * reject(AL0104,AL0111,AL0224)
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 F1 review, bodies)
codeunit 50100 T
{
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
                ;
            2:
                V(1, 3.0);
        end;
    end;

    procedure V(I: Integer; D: Decimal)
    begin
    end;
}
