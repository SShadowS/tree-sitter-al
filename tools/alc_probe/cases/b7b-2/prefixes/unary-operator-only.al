// B7b-2 final review (Important 1): a group whose only arm content is a unary operator: `I := #if X - #endif 1;`, `B := Ok and #if Y not #endif Ok;`, `if #if Z not #endif Ok then;`. alc accepts every configuration; the parser ERRORs on all three, on main and on the branch (docs/deferred-work.md item 61)
// expect: * accept
// source: B7b-2 final whole-branch review, 2026-10-21 (reviewer probe scratchpad alc/unary-op-only.al; the `if` statement added in the fix round), alc 18.0.41 four-way probe
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; B: Boolean; Ok: Boolean;
    begin
        I :=
#if X
        -
#endif
        1;
        B := Ok and
#if Y
        not
#endif
        Ok;
        if
#if Z
        not
#endif
        Ok then;
    end;
}
