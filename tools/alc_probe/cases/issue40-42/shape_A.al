// expect: !C accept
// expect: C reject(AL0104,AL0198)
// source: issue #40 shape A (invented). With C defined the split `if A then begin` drops out and leaves a stray `end;`.
codeunit 50000 "Limit Repro"
{
    procedure P(S: Boolean; T: Boolean; A: Boolean)
    begin
        if S then begin
            Q();
#if not C
            if A then begin
#endif
            end;
            Q();
        end else if T then begin
            Q();
#if not C
            if A then begin
#endif
            end;
            Q();
        end else begin
            Q();
#if not C
            if A then begin
#endif
            end;
            Q();
        end;
    end;

    procedure Q()
    begin
    end;
}
